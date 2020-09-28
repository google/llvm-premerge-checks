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
import os
import yaml

if __name__ == '__main__':
    scripts_branch = os.getenv("scripts_branch", "master")
    queue_prefix = os.getenv("ph_queue_prefix", "")
    no_cache = os.getenv('ph_no_cache') is not None
    filter_output = '--filter-output' if os.getenv('ph_no_filter_output') is None else ''
    projects = os.getenv('ph_projects', 'clang;clang-tools-extra;libc;libcxx;libcxxabi;lld;libunwind;mlir;openmp;polly')
    log_level = os.getenv('ph_log_level', 'WARNING')
    notify_emails = list(filter(None, os.getenv('ph_notify_emails', '').split(',')))
    steps = []
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
            'export SRC=${BUILDKITE_BUILD_PATH}/llvm-premerge-checks',
            'rm -rf ${SRC}',
            f'git clone --depth 1 --branch {scripts_branch} https://github.com/google/llvm-premerge-checks.git '
            '${SRC}',
            'echo "llvm-premerge-checks commit"',
            'git --git-dir ${SRC}/.git rev-parse HEAD',
            'set +e',
            f'${{SRC}}/scripts/premerge_checks.py --projects="{projects}" --log-level={log_level} {filter_output}',
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
    # FIXME: openmp is removed as it constantly fails. Make this project list be evaluated through "choose_projects".
    projects = os.getenv('ph_projects', 'clang;clang-tools-extra;libc;libcxx;libcxxabi;lld;libunwind;mlir;polly')
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
            'set SRC=%BUILDKITE_BUILD_PATH%/llvm-premerge-checks',
            'rm -rf %SRC%',
            f'git clone --depth 1 --branch {scripts_branch} https://github.com/google/llvm-premerge-checks.git %SRC%',
            'echo llvm-premerge-checks commit:',
            'git --git-dir %SRC%/.git rev-parse HEAD',
            'powershell -command "'
            f'%SRC%/scripts/premerge_checks.py --projects=\'{projects}\' --log-level={log_level} {filter_output}; '
            '\\$exit=\\$?;'
            'echo \'--- sccache stats\';'
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
    # TODO: windows builds are temporary disabled #243
    # if os.getenv('ph_skip_windows') is None:
    #     steps.append(windows_buld_step)
    notify = []
    for e in notify_emails:
        notify.append({'email': e})
    print(yaml.dump({'steps': steps, 'notify': notify}))
