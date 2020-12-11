#!/usr/bin/env python3
# Copyright 2020 Google LLC
#
# Licensed under the the Apache License v2.0 with LLVM Exceptions (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://llvm.org/LICENSE.txt
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Runs all check on buildkite agent.
import argparse
import json
import logging
import os
import pathlib
import re
import shutil
import sys
import time
from functools import partial
from typing import Callable

import clang_format_report
import clang_tidy_report
import run_cmake
from buildkite_utils import upload_file, annotate, strip_emojis
from exec_utils import watch_shell, if_not_matches, tee
from phabtalk.phabtalk import Report, PhabTalk, Step


def ninja_all_report(step: Step, _: Report):
    step.reproduce_commands.append('ninja all')
    rc = watch_shell(
        sys.stdout.buffer.write,
        sys.stderr.buffer.write,
        'ninja all', cwd=build_dir)
    logging.debug(f'ninja all: returned {rc}')
    step.set_status_from_exit_code(rc)


def ninja_check_all_report(step: Step, _: Report):
    print('Full log will be available in Artifacts "ninja-check-all.log"', flush=True)
    step.reproduce_commands.append('ninja check-all')
    rc = watch_shell(
        sys.stdout.buffer.write,
        sys.stderr.buffer.write,
        'ninja check-all', cwd=build_dir)
    logging.debug(f'ninja check-all: returned {rc}')
    step.set_status_from_exit_code(rc)


def run_step(name: str, report: Report, thunk: Callable[[Step, Report], None]) -> Step:
    start = time.time()
    print(f'---  {name}', flush=True)  # New section in Buildkite log.
    step = Step()
    step.name = name
    thunk(step, report)
    step.duration = time.time() - start
    # Expand section if step has failed.
    if not step.success:
        print('^^^ +++', flush=True)
    if step.success:
        annotate(f"{name}: OK")
    else:
        annotate(f"{name}: FAILED", style='error')
        report.success = False
    report.steps.append(step)
    return step


def cmake_report(projects: str, step: Step, _: Report):
    global build_dir
    cmake_result, build_dir, cmake_artifacts, commands = run_cmake.run(projects, os.getcwd())
    for file in cmake_artifacts:
        if os.path.exists(file):
            shutil.copy2(file, artifacts_dir)
    step.set_status_from_exit_code(cmake_result)
    step.reproduce_commands = commands


def as_dict(obj):
    try:
        return obj.toJSON()
    except:
        return obj.__dict__


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Runs premerge checks8')
    parser.add_argument('--log-level', type=str, default='WARNING')
    parser.add_argument('--check-clang-format', action='store_true')
    parser.add_argument('--check-clang-tidy', action='store_true')
    parser.add_argument('--projects', type=str, default='detect',
                        help="Projects to select, either a list or projects like 'clang;libc', or "
                             "'detect' to automatically infer proejcts from the diff, or "
                             "'default' to add all enabled projects")
    args = parser.parse_args()
    logging.basicConfig(level=args.log_level, format='%(levelname)-7s %(message)s')

    ctx = strip_emojis(os.getenv('BUILDKITE_LABEL', 'default'))
    annotate(os.getenv('BUILDKITE_LABEL', 'default'), context=ctx)
    build_dir = ''
    step_key = os.getenv("BUILDKITE_STEP_KEY")
    scripts_dir = pathlib.Path(__file__).parent.absolute()
    artifacts_dir = os.path.join(os.getcwd(), 'artifacts')
    os.makedirs(artifacts_dir, exist_ok=True)
    report_path = f'{step_key}_result.json'
    report = Report()
    report.os = f'{os.getenv("BUILDKITE_AGENT_META_DATA_OS")}'
    report.name = step_key
    report.success = True

    cmake = run_step('cmake', report, lambda s, r: cmake_report(args.projects, s, r))
    commands_in_build = True
    if cmake.success:
        ninja_all = run_step('ninja all', report, ninja_all_report)
        if ninja_all.success:
            run_step('ninja check-all', report, ninja_check_all_report)
        if args.check_clang_tidy:
            if commands_in_build:
                s = Step('')
                s.reproduce_commands.append('cd ..')
                commands_in_build = False
                report.steps.append(s)
            run_step('clang-tidy', report,
                     lambda s, r: clang_tidy_report.run('HEAD~1', os.path.join(scripts_dir, 'clang-tidy.ignore'), s, r))
    if args.check_clang_format:
        if commands_in_build:
            s = Step('')
            s.reproduce_commands.append('cd ..')
            commands_in_build = False
            report.steps.append(s)
        run_step('clang-format', report,
                 lambda s, r: clang_format_report.run('HEAD~1', os.path.join(scripts_dir, 'clang-format.ignore'), s, r))
    logging.debug(report)
    summary = []
    summary.append('''
<details>
  <summary>Reproduce build locally</summary>

```''')
    summary.append(f'git clone {os.getenv("BUILDKITE_REPO")} llvm-project')
    summary.append('cd llvm-project')
    summary.append(f'git checkout {os.getenv("BUILDKITE_COMMIT")}')
    for s in report.steps:
        if len(s.reproduce_commands) == 0:
            continue
        summary.append('\n'.join(s.reproduce_commands))
    summary.append('```\n</details>')
    annotate('\n'.join(summary), style='success')
    ph_target_phid = os.getenv('ph_target_phid')
    if ph_target_phid is not None:
        phabtalk = PhabTalk(os.getenv('CONDUIT_TOKEN'), dry_run_updates=(os.getenv('ph_dry_run_report') is not None))
        phabtalk.update_build_status(ph_target_phid, True, report.success, report.lint, [])
        for a in report.artifacts:
            url = upload_file(a['dir'], a['file'])
            if url is not None:
                phabtalk.maybe_add_url_artifact(ph_target_phid, url, f'{a["name"]} ({step_key})')
    else:
        logging.warning('ph_target_phid is not specified. Will not update the build status in Phabricator')
    with open(report_path, 'w') as f:
        json.dump(report.__dict__, f, default=as_dict)

    if not report.success:
        print('Build completed with failures', flush=True)
        exit(1)
