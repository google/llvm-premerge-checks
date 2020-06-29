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
    diff_id = os.getenv("ph_buildable_diff", "")
    steps = []
    linux_buld_step = {
        'label': ':linux: build and test linux',
        'key': 'linux',
        'commands': [
            'mkdir -p artifacts',
            'dpkg -l >> artifacts/packages.txt',
            'export SRC=${BUILDKITE_BUILD_PATH}/llvm-premerge-checks',
            'rm -rf ${SRC}',
            'git clone --depth 1 --branch ${scripts_branch} https://github.com/google/llvm-premerge-checks.git ${SRC}',
            # Add link in review to the build.
            '${SRC}/scripts/phabtalk/add_url_artifact.py '
            '--phid="$ph_target_phid" '
            '--url="$BUILDKITE_BUILD_URL" '
            '--name="Buildkite build"',
            '${SRC}/scripts/premerge_checks.py --check-clang-format --check-clang-tidy',
        ],
        'artifact_paths': ['artifacts/**/*', '*_result.json'],
        'agents': {'queue': f'{queue_prefix}linux'},
        'timeout_in_minutes': 120,
    }
    windows_buld_step = {
        'label': ':windows: build and test windows',
        'key': 'windows',
        'commands': [
            'sccache --zero-stats',
            'set SRC=%BUILDKITE_BUILD_PATH%/llvm-premerge-checks',
            'rm -rf %SRC%',
            'git clone --depth 1 --branch %scripts_branch% https://github.com/google/llvm-premerge-checks.git %SRC%',
            'powershell -command "%SRC%/scripts/premerge_checks.py; '
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
        'agents': {'queue': f'{queue_prefix}windows'},
        'timeout_in_minutes': 120,
    }
    steps.append(linux_buld_step)
    steps.append(windows_buld_step)
    report_step = {
        'label': ':spiral_note_pad: report',
        'depends_on': [linux_buld_step['key'], windows_buld_step['key']],
        'commands': [
            'mkdir -p artifacts',
            'buildkite-agent artifact download "*_result.json" .',
            'export SRC=${BUILDKITE_BUILD_PATH}/llvm-premerge-checks',
            'rm -rf ${SRC}',
            'git clone --depth 1 --branch ${scripts_branch} https://github.com/google/llvm-premerge-checks.git ${SRC}',
            '${SRC}/scripts/buildkite/summary.py',
        ],
        'allow_dependency_failure': True,
        'artifact_paths': ['artifacts/**/*'],
        'agents': {'queue': f'{queue_prefix}linux'},
        'timeout_in_minutes': 10,
    }
    steps.append(report_step)
    print(yaml.dump({'steps': steps}))
