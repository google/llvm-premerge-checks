#!/usr/bin/env bash
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

cat << EOF
steps:
  - label: "bootstrap"
    commands:
    - "git clone --depth 1 --branch \"${PREMERGE_SCRIPTS_BRANCH}\" https://github.com/google/llvm-premerge-checks.git"
    - "llvm-premerge-checks/scripts/buildkite/create_pipeline.py | tee /dev/tty | buildkite-agent pipeline upload"
    agents:
        queue: "${BUILDKITE_AGENT_META_DATA_QUEUE}"
        os: "linux"
EOF