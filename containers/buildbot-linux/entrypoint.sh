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
set -eu
set -o pipefail

USER=runner
WORKDIR=/build
chown -R ${USER}:${USER} "$WORKDIR"

export CCACHE_DIR="${WORKDIR}"/ccache
export CCACHE_MAXSIZE=20G
mkdir -p "${CCACHE_DIR}"
chown -R ${USER}:${USER} "${CCACHE_DIR}"

export SCCACHE_DIR="$WORKDIR/sccache"
export SCCACHE_IDLE_TIMEOUT="0"
rm -rf "$SCCACHE_DIR"
mkdir -p "${SCCACHE_DIR}"
chown -R ${USER}:${USER} "${SCCACHE_DIR}"
chmod oug+rw "${SCCACHE_DIR}"
gosu "$USER" bash -c 'SCCACHE_DIR="${SCCACHE_DIR}" SCCACHE_IDLE_TIMEOUT=0 SCCACHE_CACHE_SIZE=20G sccache --start-server'

# configure buildbot
mkdir -p /build/buildbot
if [[ -z "${BUILDBOT_ADDRESS+x}" ]]; then
  echo "Not starting buildbot as BUILDBOT_ADDRESS is not set"
else
  buildbot-worker create-worker /build/buildbot $BUILDBOT_ADDRESS $BUILDBOT_NAME $BUILDBOT_PASSWORD
  unset BUILDBOT_ADDRESS
  unset BUILDBOT_NAME
  unset BUILDBOT_PASSWORD
  echo "llvm-premerge-buildbots <llvm-premerge-buildbots@google.com>, Mikhail Goncharov<goncharov.mikhail@gmail.com>" > /build/buildbot/info/admin
  echo "Setup analogous to linux agent for Pull Request checks:" > /build/buildbot/info/host
  echo "GCP machine c2d-standard-56 56vCPU 224Gb" >> /build/buildbot/info/host
  echo "Ubuntu 20 cmake-3.23.3 python-3.10 ninja-1.10.1 LLVM-16" >> /build/buildbot/info/host
  echo "https://github.com/google/llvm-premerge-checks/blob/main/containers/buildbot-linux/Dockerfile" >> /build/buildbot/info/host
  chown -R ${USER}:${USER} /build/buildbot
  gosu "$USER" bash -c 'CC=clang CXX=clang++ LD=LLD buildbot-worker start /build/buildbot'
fi

# Run with tini to correctly pass exit codes.
exec /usr/bin/tini -g -- $@
