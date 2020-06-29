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
    queue_prefix = os.getenv("ph_queue_prefix", "")
    diff_id = os.getenv("ph_buildable_diff")
    steps = []
    create_branch_step = {
        'label': 'create branch',
        'key': 'create-branch',
        'commands': ['scripts/buildkite/apply_patch.sh'],
        'agents': {'queue': f'{queue_prefix}linux'},
        'timeout_in_minutes': 20,
    }
    build_linux_step = {
        'trigger': 'premerge-checks',
        'label': ':rocket: build and test',
        'async': False,
        'depends_on': 'create-branch',
        'build': {
            'branch': f'phab-diff-{diff_id}',
            'env': {'scripts_branch': '${BUILDKITE_BRANCH}'},
        },
    }
    for e in os.environ:
        if e.startswith('ph_'):
            build_linux_step['build']['env'][e] = os.getenv(e)
    steps.append(create_branch_step)
    steps.append(build_linux_step)
    print(yaml.dump({'steps': steps}))
