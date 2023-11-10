#!/usr/bin/env bash

# Copyright 2023 Google LLC
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
set -ueo pipefail

export PATH=${PATH}:/home/runner

USER=runner
WORKDIR=${WORKDIR:-/home/runner/_work}

export SCCACHE_DIR="${WORKDIR}/sccache"
mkdir -p "${SCCACHE_DIR}"
chown -R ${USER}:${USER} "${SCCACHE_DIR}"
chmod oug+rw "${SCCACHE_DIR}"
gosu runner bash -c 'SCCACHE_DIR="${SCCACHE_DIR}" SCCACHE_IDLE_TIMEOUT=0 SCCACHE_CACHE_SIZE=20G sccache --start-server'
sccache --show-stats

[[ ! -d "${WORKDIR}" ]] && mkdir -p "${WORKDIR}"

# exec /usr/bin/tini -g -- $@
gosu runner "$@"
