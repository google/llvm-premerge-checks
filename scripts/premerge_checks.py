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
import shutil
import subprocess
import time
from typing import Callable

import clang_format_report
import clang_tidy_report
import run_cmake
import test_results_report
from buildkite.utils import upload_file
from phabtalk.add_url_artifact import maybe_add_url_artifact
from phabtalk.phabtalk import Report, PhabTalk, Step


def ninja_all_report(step: Step, _: Report):
    print('Full will be available in Artifacts "ninja-all.log"')
    r = subprocess.run(f'ninja all | '
                       f'tee {artifacts_dir}/ninja-all.log | '
                       f'grep -vE "\\[.*] (Building|Linking|Copying|Generating|Creating)"',
                       shell=True, cwd=build_dir)
    logging.debug(f'ninja all: returned {r.returncode}, stderr: "{r.stderr}"')
    step.set_status_from_exit_code(r.returncode)


def ninja_check_all_report(step: Step, _: Report):
    print('Full will be available in Artifacts "ninja-check-all.log"')
    r = subprocess.run(f'ninja check-all | tee {artifacts_dir}/ninja-check-all.log | '
                       f'grep -vE "^\\[.*] (Building|Linking)" | '
                       f'grep -vE "^(PASS|XFAIL|UNSUPPORTED):"', shell=True, cwd=build_dir)
    logging.debug(f'ninja check-all: returned {r.returncode}, stderr: "{r.stderr}"')
    step.set_status_from_exit_code(r.returncode)
    test_results_report.run(build_dir, 'test-results.xml', step, report)


def run_step(name: str, report: Report, thunk: Callable[[Step, Report], None]) -> Step:
    start = time.time()
    print(f'---  {name}')  # New section in Buildkite log.
    step = Step()
    step.name = name
    thunk(step, report)
    step.duration = time.time() - start
    # Expand section if it failed.
    if not step.success:
        print('^^^ +++')
    report.steps.append(step)
    return step


def cmake_report(step: Step, _: Report):
    global build_dir
    cmake_result, build_dir, cmake_artifacts = run_cmake.run('detect', os.getcwd())
    for file in cmake_artifacts:
        if os.path.exists(file):
            shutil.copy2(file, artifacts_dir)
    step.set_status_from_exit_code(cmake_result)


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
    args = parser.parse_args()
    logging.basicConfig(level=args.log_level, format='%(levelname)-7s %(message)s')
    build_dir = ''
    step_key = os.getenv("BUILDKITE_STEP_KEY")
    scripts_dir = pathlib.Path(__file__).parent.absolute()
    artifacts_dir = os.path.join(os.getcwd(), 'artifacts')
    os.makedirs(artifacts_dir, exist_ok=True)
    report_path = f'{step_key}_result.json'
    report = Report()
    report.os = f'{os.getenv("BUILDKITE_AGENT_META_DATA_OS")}'
    report.name = step_key
    report.success = False
    # Create report with failure in case something below fails.
    with open(report_path, 'w') as f:
        json.dump(report.__dict__, f, default=as_dict)
    report.success = True
    cmake = run_step('cmake', report, cmake_report)
    if cmake.success:
        ninja_all = run_step('ninja all', report, ninja_all_report)
        if ninja_all.success:
            run_step('ninja check-all', report, ninja_check_all_report)
        if args.check_clang_tidy:
            run_step('clang-tidy', report,
                     lambda s, r: clang_tidy_report.run('HEAD~1', os.path.join(scripts_dir, 'clang-tidy.ignore'), s, r))
    if args.check_clang_format:
        run_step('clang-format', report,
                 lambda s, r: clang_format_report.run('HEAD~1', os.path.join(scripts_dir, 'clang-format.ignore'), s, r))
    logging.debug(report)
    for s in report.steps:
        mark = 'OK   '
        if not s.success:
            report.success = False
            mark = 'FAIL '
        msg = ''
        if len(s.messages):
            msg = ': ' + '\n  '.join(s.messages)
        print(f'{mark} {s.name}{msg}')

    ph_target_phid = os.getenv('ph_target_phid')
    ph_buildable_diff = os.getenv('ph_buildable_diff')
    if ph_target_phid is not None:
        phabtalk = PhabTalk(os.getenv('CONDUIT_TOKEN'), 'https://reviews.llvm.org/api/', False)
        for u in report.unit:
            u['engine'] = step_key
        phabtalk.update_build_status(ph_buildable_diff, ph_target_phid, True, report.success, report.lint, report.unit)
        for a in report.artifacts:
            url = upload_file(a['dir'], a['file'])
            if url is not None:
                maybe_add_url_artifact(phabtalk, ph_target_phid, url, f'{a["name"]} (${step_key})')
    else:
        logging.warning('No phabricator phid is specified. Will not update the build status in Phabricator')
    with open(report_path, 'w') as f:
        json.dump(report.__dict__, f, default=as_dict)
    if not report.success:
        print('Build completed with failures')
        exit(1)
