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

import os
import yaml

if __name__ == '__main__':
    script_branch = os.getenv("scripts_branch", "master")
    queue_prefix = os.getenv("ph_queue_prefix", "")
    no_cache = os.getenv('ph_no_cache', '') != ''
    projects = os.getenv('ph_projects', 'clang;clang-tools-extra;libc;libcxx;libcxxabi;lld;libunwind;mlir;openmp;polly')
    log_level = os.getenv('ph_log_level', 'WARNING')
    steps = []
    linux_buld_step = {
        'label': ':linux: build and test linux',
        'key': 'linux',
        'commands': [
            'set -euo pipefail',
            'ccache --clear' if no_cache else '',
            'ccache --zero-stats',
            'mkdir -p artifacts',
            'dpkg -l >> artifacts/packages.txt',
            'export SRC=${BUILDKITE_BUILD_PATH}/llvm-premerge-checks',
            'rm -rf ${SRC}',
            'git clone --depth 1 --branch ${scripts_branch} https://github.com/google/llvm-premerge-checks.git ${SRC}',
            'set -eo pipefail',
            f'${{SRC}}/scripts/premerge_checks.py --projects="{projects}" --log-level={log_level}',
            'EXIT_STATUS=\\$?',
            'echo "--- ccache stats"',
            'ccache --show-stats',
            'exit \\$EXIT_STATUS',
        ],
        'artifact_paths': ['artifacts/**/*', '*_result.json'],
        'agents': {'queue': f'{queue_prefix}linux'},
        'timeout_in_minutes': 120,
    }
    clear_sccache = 'powershell -command "sccache --stop-server; ' \
                    'Remove-Item -Recurse -Force -ErrorAction Ignore $env:SCCACHE_DIR; ' \
                    'sccache --start-server"'
    # FIXME: openmp is removed as it constantly fails.
    projects = os.getenv('ph_projects', 'clang;clang-tools-extra;libc;libcxx;libcxxabi;lld;libunwind;mlir;polly')
    windows_buld_step = {
        'label': ':windows: build and test windows',
        'key': 'windows',
        'commands': [
            clear_sccache if no_cache else '',
            'sccache --zero-stats',
            'set SRC=%BUILDKITE_BUILD_PATH%/llvm-premerge-checks',
            'rm -rf %SRC%',
            'git clone --depth 1 --branch %scripts_branch% https://github.com/google/llvm-premerge-checks.git %SRC%',
            f'powershell -command "%SRC%/scripts/premerge_checks.py --projects=\'{projects}\' --log-level={log_level}; '
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
        'agents': {'queue': f'{queue_prefix}windows'},
        'timeout_in_minutes': 120,
    }
    steps.append(linux_buld_step)
    steps.append(windows_buld_step)
    print(yaml.dump({'steps': steps}))
