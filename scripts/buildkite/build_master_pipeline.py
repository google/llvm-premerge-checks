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
    queue = os.getenv("BUILDKITE_AGENT_META_DATA_QUEUE", "default")
    diff_id = os.getenv("ph_buildable_diff", "")
    steps = []
    linux_buld_step = {
        'label': ':linux: build and test linux',
        'key': 'linux',
        'commands': [
            'export SRC=${BUILDKITE_BUILD_PATH}/llvm-premerge-checks',
            'rm -rf ${SRC}',
            'git clone --depth 1 --branch ${scripts_branch} https://github.com/google/llvm-premerge-checks.git ${SRC}',
            '${SRC}/scripts/premerge_checks.py --check-clang-format --check-clang-tidy '
            '--projects="clang;clang-tools-extra;libc;libcxx;libcxxabi;lld;libunwind;mlir;flang"',
        ],
        'artifact_paths': ['artifacts/**/*', '*_result.json'],
        'agents': {'queue': queue, 'os': 'linux'}
    }
    windows_buld_step = {
        'label': ':windows: build and test windows',
        'key': 'windows',
        'commands': [
            'sccache --zero-stats',
            'set SRC=%BUILDKITE_BUILD_PATH%/llvm-premerge-checks',
            'rm -rf %SRC%',
            'git clone --depth 1 --branch %scripts_branch% https://github.com/google/llvm-premerge-checks.git %SRC%',
            'powershell -command "%SRC%/scripts/premerge_checks.py --projects=default; '
            '\\$exit=\\$?;'
            'sccache --show-stats;'
            'if (\\$exit) {'
            '  echo "success";'
            '  exit 0; } '
            'else {'
            '  echo "failure";'
            '  exit 1;'
            '}',
        ],
        'artifact_paths': ['artifacts/**/*', '*_result.json'],
        'agents': {'queue': queue, 'os': 'windows'},
    }
    steps.append(linux_buld_step)
    steps.append(windows_buld_step)
    print(yaml.dump({'steps': steps}))
