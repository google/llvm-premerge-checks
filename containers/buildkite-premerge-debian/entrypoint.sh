#!/usr/bin/env bash

# Copyright 2021 Google LLC
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
set -eo pipefail

USER=buildkite-agent
P="${BUILDKITE_BUILD_PATH:-/var/lib/buildkite-agent}"
set -u
mkdir -p "$P"
chown -R ${USER}:${USER} "$P"

export CCACHE_DIR="${P}"/ccache
export CCACHE_MAXSIZE=20G
mkdir -p "${CCACHE_DIR}"
chown -R ${USER}:${USER} "${CCACHE_DIR}"

# /mnt/ssh should contain known_hosts, id_rsa and id_rsa.pub .
mkdir -p /var/lib/buildkite-agent/.ssh
if [ -d /mnt/ssh ]; then
  cp /mnt/ssh/* /var/lib/buildkite-agent/.ssh || echo "no "
  chmod 700 /var/lib/buildkite-agent/.ssh
  chmod 600 /var/lib/buildkite-agent/.ssh/*
  chown -R buildkite-agent:buildkite-agent /var/lib/buildkite-agent/.ssh/
else
  echo "/mnt/ssh is not mounted"
fi
exec /usr/bin/tini -g -- $@
