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

import logging
import os

from choose_projects import ChooseProjects
import git
from steps import libcxx, generic_linux, generic_windows
import yaml

if __name__ == '__main__':
    scripts_refspec = os.getenv("ph_scripts_refspec", "master")
    diff_id = os.getenv("ph_buildable_diff", "")
    no_cache = os.getenv('ph_no_cache') is not None
    filter_output = '--filter-output' if os.getenv('ph_no_filter_output') is None else ''
    projects = os.getenv('ph_projects', 'detect')
    log_level = os.getenv('ph_log_level', 'INFO')
    logging.basicConfig(level=log_level, format='%(levelname)-7s %(message)s')

    # List all affected projects.
    repo = git.Repo('.')
    patch = repo.git.diff("HEAD~1")
    cp = ChooseProjects('.')
    modified_files = cp.get_changed_files(patch)
    modified_projects, unmapped_changes = cp.get_changed_projects(modified_files)
    if unmapped_changes:
        logging.warning('There were changes that could not be mapped to a project. Checking everything')
        modified_projects = cp.all_projects
    logging.info(f'modified projects: {modified_projects}')
    # Add projects that depend on modified.
    affected_projects = cp.get_affected_projects(modified_projects)

    # Handle special checks.
    checked = set()
    generic_projects = set()
    logging.info(f'all affected projects: {affected_projects}')
    steps = []
    for p in affected_projects:
        if p == 'libcxx' or p == 'libcxxabi':
            if 'libcxx' not in checked:
                logging.info('Adding custom steps for "libc++"')
                checked.add('libcxx')
                steps.extend(libcxx())
        else:
            generic_projects.add(p)

    if len(generic_projects) > 0:
        # Add dependencies
        projects = ';'.join(sorted(cp.add_dependencies(generic_projects)))
        logging.info(f'Projects for default checks: {projects}')
        steps.extend(generic_linux(projects, True))
        steps.extend(generic_windows(projects))
    else:
        logging.info('No projects for default checks')

    deps = []

    steps.append({
        'wait': '~',
        'continue_on_failure': True,
    })

    report_step = {
        'label': ':spiral_note_pad: report',
        'commands': [
            'mkdir -p artifacts',
            'buildkite-agent artifact download "*_result.json" .',

            # Clone scripts.
            'export SRC=${BUILDKITE_BUILD_PATH}/llvm-premerge-checks',
            'rm -rf ${SRC}',
            'git clone --depth 1 https://github.com/google/llvm-premerge-checks.git "${SRC}"',
            'cd ${SRC}',
            f'git fetch origin "{scripts_refspec}":x',
            'git checkout x',
            'echo "llvm-premerge-checks commit"',
            'git rev-parse HEAD',
            'cd "$BUILDKITE_BUILD_CHECKOUT_PATH"',
            '${SRC}/scripts/summary.py',
        ],
        'artifact_paths': ['artifacts/**/*'],
        'agents': {'queue': 'linux'},
        'timeout_in_minutes': 10,
    }
    steps.append(report_step)
    print(yaml.dump({'steps': steps}))
