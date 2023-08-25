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

export PATH=${PATH}:/actions-runner

USER=runner
RUNNER_WORKDIR="/_work"
set -u

export SCCACHE_DIR="${RUNNER_WORKDIR}/sccache"
mkdir -p "${SCCACHE_DIR}"
chown -R ${USER}:${USER} "${SCCACHE_DIR}"
chmod oug+rw "${SCCACHE_DIR}"
gosu runner bash -c 'SCCACHE_DIR="${SCCACHE_DIR}" SCCACHE_IDLE_TIMEOUT=0 SCCACHE_CACHE_SIZE=20G sccache --start-server'
sccache --show-stats
_RUNNER_NAME=${RUNNER_NAME:-${RUNNER_NAME_PREFIX:-github-runner}-$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 13 ; echo '')}
echo "Configuring"
echo "runner URL" "${ACTION_RUNNER_URL}"
echo "runner token" "${ACTION_RUNNER_TOKEN}"
echo "runner name" "${_RUNNER_NAME}"
gosu runner ./config.sh \
    --url "${ACTION_RUNNER_URL}" \
    --token "${ACTION_RUNNER_TOKEN}" \
    --name "${_RUNNER_NAME}" \
    --work "${RUNNER_WORKDIR}" \
    --labels "${ACTION_RUNNER_LABEL}" \
    --unattended \
    --replace

# exec /usr/bin/tini -g -- $@
gosu runner "$@"
