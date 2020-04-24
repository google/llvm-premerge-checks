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

if __name__ == '__main__':
    script_branch = os.getenv("PREMERGE_SCRIPTS_BRANCH", "master")
    queue = os.getenv("BUILDKITE_AGENT_META_DATA_QUEUE", "default")
    print(f"""
  steps:
    - label: "build"
      commands:
      - "git clone --depth 1 --branch '{script_branch}' https://github.com/google/llvm-premerge-checks.git"
      - "llvm-premerge-checks/scripts/run_buildkite.sh"
      agents:
          queue: "{queue}"
          os: "linux"
    - label: "parallel step"
      commands:
      - "echo do nothing"
      agents:
          queue: "{queue}"
          os: "linux"
    """)
