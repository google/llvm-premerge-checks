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

import json
import logging
import os

from choose_projects import ChooseProjects
import git
import yaml

if __name__ == '__main__':
    scripts_refspec = os.getenv("ph_scripts_refspec", "master")
    queue_prefix = os.getenv("ph_queue_prefix", "")
    diff_id = os.getenv("ph_buildable_diff", "")
    no_cache = os.getenv('ph_no_cache') is not None
    filter_output = '--filter-output' if os.getenv('ph_no_filter_output') is None else ''
    projects = os.getenv('ph_projects', 'detect')
    log_level = os.getenv('ph_log_level', 'WARNING')
    logging.basicConfig(level=log_level, format='%(levelname)-7s %(message)s')

    # List all affected projects.
    repo = git.Repo('.')
    patch = repo.git.diff("HEAD~1")
    cp = ChooseProjects('.')
    affected_projects = cp.choose_projects(patch)
    print('# all affected projects')
    for p in affected_projects:
        print(f'# {p}')

    steps = []
    deps = []

    if 'libcxx' in affected_projects or 'libcxxabi' in affected_projects:
        start_libcxx_step = {
            'trigger': 'libcxx-ci',
            'label': 'libcxx',
            'key': 'libcxx',
            'async': False,
            'build': {
                'branch': os.getenv('BUILDKITE_BRANCH'),
                'env': {},
            },
        }
        for e in os.environ:
            if e.startswith('ph_'):
                start_libcxx_step['build']['env'][e] = os.getenv(e)
        steps.append(start_libcxx_step)
        deps.append(start_libcxx_step['key'])

    linux_agents = {'queue': f'{queue_prefix}linux'}
    t = os.getenv('ph_linux_agents')
    if t is not None:
        linux_agents = json.loads(t)
    linux_buld_step = {
        'label': ':linux: build and test linux',
        'key': 'linux',
        'commands': [
            'set -euo pipefail',
            'ccache --clear' if no_cache else '',
            'ccache --zero-stats',
            'ccache --show-config',
            'mkdir -p artifacts',
            'dpkg -l >> artifacts/packages.txt',
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

            'set +e',
            # Add link in review to the build.
            '${SRC}/scripts/add_phabricator_artifact.py '
            '--phid="$ph_target_phid" '
            '--url="$BUILDKITE_BUILD_URL" '
            '--name="Buildkite build"',
            '${SRC}/scripts/premerge_checks.py --check-clang-format --check-clang-tidy '
            f'--projects="{projects}" --log-level={log_level} {filter_output}',
            'EXIT_STATUS=\\$?',
            'echo "--- ccache stats"',
            'ccache --print-stats',
            'ccache --show-stats',
            'exit \\$EXIT_STATUS',
        ],
        'artifact_paths': ['artifacts/**/*', '*_result.json'],
        'agents': linux_agents,
        'timeout_in_minutes': 120,
        'retry': {'automatic': [
            {'exit_status': -1, 'limit': 2},  # Agent lost
            {'exit_status': 255, 'limit': 2},  # Forced agent shutdown
        ]},
    }
    clear_sccache = 'powershell -command "sccache --stop-server; echo \\$env:SCCACHE_DIR; ' \
                    'Remove-Item -Recurse -Force -ErrorAction Ignore \\$env:SCCACHE_DIR; ' \
                    'sccache --start-server"'
    win_agents = {'queue': f'{queue_prefix}windows'}
    t = os.getenv('ph_windows_agents')
    if t is not None:
        win_agents = json.loads(t)
    windows_buld_step = {
        'label': ':windows: build and test windows',
        'key': 'windows',
        'commands': [
            clear_sccache if no_cache else '',
            'sccache --zero-stats',

            # Clone scripts.
            'set SRC=%BUILDKITE_BUILD_PATH%/llvm-premerge-checks',
            'rm -rf %SRC%',
            'git clone --depth 1 https://github.com/google/llvm-premerge-checks.git %SRC%',
            'cd %SRC%',
            f'git fetch origin "{scripts_refspec}":x',
            'git checkout x',
            'echo llvm-premerge-checks commit:',
            'git rev-parse HEAD',
            'cd %BUILDKITE_BUILD_CHECKOUT_PATH%',

            'powershell -command "'
            f'%SRC%/scripts/premerge_checks.py --projects=\'{projects}\' --log-level={log_level} {filter_output}; '
            '\\$exit=\\$?;'
            'sccache --show-stats;'
            'if (\\$exit) {'
            '  echo success;'
            '  exit 0; } '
            'else {'
            '  echo failure;'
            '  exit 1;'
            '}"',
        ],
        'artifact_paths': ['artifacts/**/*', '*_result.json'],
        'agents': win_agents,
        'timeout_in_minutes': 120,
        'retry': {'automatic': [
            {'exit_status': -1, 'limit': 2},  # Agent lost
            {'exit_status': 255, 'limit': 2},  # Forced agent shutdown
        ]},
    }
    if os.getenv('ph_skip_linux') is None:
        steps.append(linux_buld_step)
        deps.append(linux_buld_step['key'])
    # TODO: windows builds are temporary disabled #243
    # if os.getenv('ph_skip_windows') is None:
    #     steps.append(windows_buld_step)
    #     deps.append(windows_buld_step['key'])
    report_step = {
        'label': ':spiral_note_pad: report',
        'depends_on': deps,
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
        'allow_dependency_failure': True,
        'artifact_paths': ['artifacts/**/*'],
        'agents': {'queue': f'{queue_prefix}linux'},
        'timeout_in_minutes': 10,
    }
    steps.append(report_step)
    print(yaml.dump({'steps': steps}))
