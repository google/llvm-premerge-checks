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

# Script runs in checked out llvm-project directory.

import logging
import os
from typing import Dict

from buildkite_utils import annotate, feedback_url, set_metadata
from choose_projects import ChooseProjects
import git
from steps import generic_linux, generic_windows, from_shell_output, checkout_scripts, bazel, extend_steps_env
import yaml

steps_generators = [
    '${BUILDKITE_BUILD_CHECKOUT_PATH}/libcxx/utils/ci/buildkite-pipeline-premerge.sh',
]

if __name__ == '__main__':
    scripts_refspec = os.getenv("ph_scripts_refspec", "main")
    diff_id = os.getenv("ph_buildable_diff", "")
    no_cache = os.getenv('ph_no_cache') is not None
    projects = os.getenv('ph_projects', 'detect')
    log_level = os.getenv('ph_log_level', 'INFO')
    logging.basicConfig(level=log_level, format='%(levelname)-7s %(message)s')

    phid = os.getenv('ph_target_phid')
    url = f"https://reviews.llvm.org/D{os.getenv('ph_buildable_revision')}?id={diff_id}"
    annotate(f"Build for [D{os.getenv('ph_buildable_revision')}#{diff_id}]({url}). "
             f"[Harbormaster build](https://reviews.llvm.org/harbormaster/build/{os.getenv('ph_build_id')}).\n"
             f"If there is a build infrastructure issue, please [create a bug]({feedback_url()}).")
    set_metadata('ph_buildable_diff', os.getenv("ph_buildable_diff"))
    set_metadata('ph_buildable_revision', os.getenv('ph_buildable_revision'))
    set_metadata('ph_build_id', os.getenv("ph_build_id"))

    env: Dict[str, str] = {}
    for e in os.environ:
        if e.startswith('ph_'):
            env[e] = os.getenv(e, '')
    repo = git.Repo('.')
    steps = []
    # List all affected projects.
    patch = repo.git.diff("HEAD~1")
    cp = ChooseProjects('.')

    linux_projects = cp.choose_projects(patch = patch, os_name = "linux")
    logging.info(f'linux_projects: {linux_projects}')
    if len(linux_projects) > 0:
        steps.extend(generic_linux(';'.join(linux_projects), check_diff=True))

    windows_projects = cp.choose_projects(patch = patch, os_name = "windows")
    logging.info(f'windows_projects: {windows_projects}')
    if len(windows_projects) > 0:
        steps.extend(generic_windows(';'.join(windows_projects)))

    # Add custom checks.
    if os.getenv('ph_skip_generated') is None:
        if os.getenv('BUILDKITE_COMMIT', 'HEAD') == "HEAD":
            env['BUILDKITE_COMMIT'] = repo.head.commit.hexsha
        for gen in steps_generators:
            steps.extend(from_shell_output(gen, env=env))
    modified_files = cp.get_changed_files(patch)
    steps.extend(bazel(modified_files))

    if phid is None:
        logging.warning('ph_target_phid is not specified. Skipping "Report" step')
    else:
        steps.append({
            'wait': '~',
            'continue_on_failure': True,
        })

        report_step = {
            'label': ':phabricator: update build status on Phabricator',
            'commands': [
                *checkout_scripts('linux', scripts_refspec),
                '$${SRC}/scripts/summary.py',
            ],
            'artifact_paths': ['artifacts/**/*'],
            'agents': {'queue': 'service'},
            'timeout_in_minutes': 10,
        }
        steps.append(report_step)

    extend_steps_env(steps, env)
    print(yaml.dump({'steps': steps}))
