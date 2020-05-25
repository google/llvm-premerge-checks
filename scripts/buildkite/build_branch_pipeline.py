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
    # SCRIPT_DIR is defined in buildkite pipeline step.
    linux_buld_step = {
        'label': 'build linux',
        'key': 'build-linux',
        'commands': [
            '${SCRIPT_DIR}/premerge_checks.py',
        ],
        'artifact_paths': ['artifacts/**/*'],
        'agents': {'queue': queue, 'os': 'linux'}
    }
    steps.append(linux_buld_step)
    print(yaml.dump({'steps': steps}))
