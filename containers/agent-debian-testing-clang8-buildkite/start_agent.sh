#!/bin/bash
# Copyright 2019 Google LLC
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

SSD_ROOT="/mnt/disks/ssd0"
AGENT_ROOT="${SSD_ROOT}/agent"

# prepare root folder for Jenkins agent
mkdir -p "${AGENT_ROOT}"
chown -R buildkite:buildkite "${AGENT_ROOT}"

# prepare folder for ccache
mkdir -p "${CCACHE_PATH}"
chown -R buildkite:buildkite "${CCACHE_PATH}"

# TODO(kuhnel): wipe the disk(s) on startup

# set the token in the config file
sed -i -r s/token=\"[^\"]+\"/token=\"`cat /credentials/buildkite-token`\"/g /etc/buildkite-agent/buildkite-agent.cfg

# start the buildkite agent
buildkite-agent start