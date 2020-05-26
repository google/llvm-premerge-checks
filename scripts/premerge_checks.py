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
import json
import logging
import os
import pathlib
import re
import shutil
import subprocess
import time
import uuid
from typing import Callable, Optional

import clang_format_report
import clang_tidy_report
import run_cmake
import test_results_report
from phabtalk.phabtalk import Report, CheckResult, PhabTalk


def upload_file(base_dir: str, file: str):
    """
    Uploads artifact to buildkite and returns URL to it
    """
    r = subprocess.run(f'buildkite-agent artifact upload "{file}"', shell=True, capture_output=True, cwd=base_dir)
    logging.debug(f'upload-artifact {r}')
    match = re.search('Uploading artifact ([^ ]*) ', r.stderr.decode())
    logging.debug(f'match {match}')
    if match:
        url = f'https://buildkite.com/organizations/llvm-project/pipelines/premerge-checks/builds/{os.getenv("BUILDKITE_BUILD_NUMBER")}/jobs/{os.getenv("BUILDKITE_JOB_ID")}/artifacts/{match.group(1)}'
        logging.info(f'uploaded {file} to {url}')
        return url
    else:
        logging.warning(f'could not find artifact {base_dir}/{file}')
        return None


def maybe_add_url_artifact(phab: PhabTalk, url: str, name: str):
    phid = os.getenv('ph_target_phid')
    if phid is None:
        return
    phab.create_artifact(phid, str(uuid.uuid4()), 'uri', {'uri': url, 'ui.external': True, 'name': name})


def add_shell_result(report: Report, name: str, exit_code: int) -> CheckResult:
    logging.info(f'"{name}" exited with {exit_code}')
    z = CheckResult.SUCCESS
    if exit_code != 0:
        z = CheckResult.FAILURE
    report.add_step(name, z, '')
    return z


def ninja_all_report(report: Report) -> CheckResult:
    print('Full will be available in Artifacts "ninja-all.log"')
    r = subprocess.run(f'ninja all | '
                       f'tee {artifacts_dir}/ninja-all.log | '
                       f'grep -vE "\\[.*] (Building|Linking|Copying|Generating|Creating)"',
                       shell=True, cwd=build_dir)
    return add_shell_result(report, 'ninja all', r.returncode)


def ninja_check_all_report(report: Report) -> CheckResult:
    # TODO: merge running ninja check all and analysing results in one step?
    print('Full will be available in Artifacts "ninja-check-all.log"')
    r = subprocess.run(f'ninja check-all | tee {artifacts_dir}/ninja-check-all.log | '
                       f'grep -vE "^\\[.*] (Building|Linking)" | '
                       f'grep -vE "^(PASS|XFAIL|UNSUPPORTED):"', shell=True, cwd=build_dir)
    z = add_shell_result(report, 'ninja check all', r.returncode)
    # TODO: check if test-results are present.
    report.add_artifact(build_dir, 'test-results.xml', 'test results')
    test_results_report.run(os.path.join(build_dir, 'test-results.xml'), report)
    return z


def run_step(name: str, report: Report, thunk: Callable[[Report], CheckResult]) -> CheckResult:
    global timings
    start = time.time()
    print(f'---  {name}')  # New section in Buildkite log.
    result = thunk(report)
    timings[name] = time.time() - start
    # Expand section if it failed.
    if result == CheckResult.FAILURE:
        print('^^^ +++')
    return result


def cmake_report(report: Report) -> CheckResult:
    global build_dir
    cmake_result, build_dir, cmake_artifacts = run_cmake.run('detect', os.getcwd())
    for file in cmake_artifacts:
        if os.path.exists(file):
            shutil.copy2(file, artifacts_dir)
    return add_shell_result(report, 'cmake', cmake_result)


def furl(url: str, name: Optional[str] = None):
    if name is None:
        name = url
    return f"\033]1339;url='{url}';content='{name}'\a\n"


if __name__ == '__main__':
    build_dir = ''
    logging.basicConfig(level=logging.WARNING, format='%(levelname)-7s %(message)s')
    scripts_dir = pathlib.Path(__file__).parent.absolute()
    phab = PhabTalk(os.getenv('CONDUIT_TOKEN'), 'https://reviews.llvm.org/api/', False)
    maybe_add_url_artifact(phab, os.getenv('BUILDKITE_BUILD_URL'), 'Buildkite build')
    artifacts_dir = os.path.join(os.getcwd(), 'artifacts')
    os.makedirs(artifacts_dir, exist_ok=True)
    report = Report()
    timings = {}
    cmake_result = run_step('cmake', report, cmake_report)
    if cmake_result == CheckResult.SUCCESS:
        compile_result = run_step('ninja all', report, ninja_all_report)
        if compile_result == CheckResult.SUCCESS:
            run_step('ninja check all', report, ninja_check_all_report)
        run_step('clang-tidy', report,
                 lambda x: clang_tidy_report.run('HEAD~1', os.path.join(scripts_dir, 'clang-tidy.ignore'), x))
    run_step('clang-format', report,
             lambda x: clang_format_report.run('HEAD~1', os.path.join(scripts_dir, 'clang-format.ignore'), x))
    print('+++ summary')
    print(f'Branch {os.getenv("BUILDKITE_BRANCH")} at {os.getenv("BUILDKITE_REPO")}')
    ph_buildable_diff = os.getenv('ph_buildable_diff')
    if ph_buildable_diff is not None:
        url = f'https://reviews.llvm.org/D{os.getenv("ph_buildable_revision")}?id={ph_buildable_diff}'
        print(f'Review: {furl(url)}')
    if os.getenv('BUILDKITE_TRIGGERED_FROM_BUILD_NUMBER') is not None:
        url = f'https://buildkite.com/llvm-project/' \
              f'{os.getenv("BUILDKITE_TRIGGERED_FROM_BUILD_PIPELINE_SLUG")}/'\
              f'builds/{os.getenv("BUILDKITE_TRIGGERED_FROM_BUILD_NUMBER")}'
        print(f'Triggered from build {furl(url)}')
    logging.debug(report)
    success = True
    for s in report.steps:
        mark = 'V'
        if s['result'] == CheckResult.UNKNOWN:
            mark = '?'
        if s['result'] == CheckResult.FAILURE:
            success = False
            mark = 'X'
        msg = s['message']
        if len(msg):
            msg = ': ' + msg
        print(f'{mark} {s["title"]}{msg}')

    # TODO: dump the report and deduplicate tests and other reports later (for multiple OS) in a separate step.
    ph_target_phid = os.getenv('ph_target_phid')
    if ph_target_phid is not None:
        build_url = f'https://reviews.llvm.org/harbormaster/build/{os.getenv("ph_build_id")}'
        print(f'Reporting results to Phabricator build {furl(build_url)}')
        phab.update_build_status(ph_buildable_diff, ph_target_phid, False, success, report.lint, report.unit)
        for a in report.artifacts:
            url = upload_file(a['dir'], a['file'])
            if url is not None:
                maybe_add_url_artifact(phab, url, a['name'])
    else:
        logging.warning('No phabricator phid is specified. Will not update the build status in Phabricator')
    # TODO: add link to report issue on github
    with open(os.path.join(artifacts_dir, 'step-timings.json'), 'w') as f:
        f.write(json.dumps(timings))
