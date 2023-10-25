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
set -ueo pipefail

export PATH=${PATH}:/actions-runner

USER=runner
WORKDIR=${WORKDIR:-/_work}

export SCCACHE_DIR="${WORKDIR}/sccache"
mkdir -p "${SCCACHE_DIR}"
chown -R ${USER}:${USER} "${SCCACHE_DIR}"
chmod oug+rw "${SCCACHE_DIR}"
gosu runner bash -c 'SCCACHE_DIR="${SCCACHE_DIR}" SCCACHE_IDLE_TIMEOUT=0 SCCACHE_CACHE_SIZE=20G sccache --start-server'
sccache --show-stats

# Configure github runner. TODO: move to a separate file.
# Based on https://github.com/myoung34/docker-github-actions-runner/blob/master/entrypoint.sh
# licensed under MIT https://github.com/myoung34/docker-github-actions-runner/blob/master/LICENSE
export -n ACCESS_TOKEN
RUNNER_SCOPE=${RUNNER_SCOPE:-repo}
RUNNER_SCOPE="${RUNNER_SCOPE,,}" # to lowercase
_GITHUB_HOST=${GITHUB_HOST:="github.com"}
case ${RUNNER_SCOPE} in
  org*)
    [[ -z ${ORG_NAME} ]] && ( echo "ORG_NAME required for org runners"; exit 1 )
    _SHORT_URL="https://${_GITHUB_HOST}/${ORG_NAME}"
    RUNNER_SCOPE="org"
    ;;

  ent*)
    [[ -z ${ENTERPRISE_NAME} ]] && ( echo "ENTERPRISE_NAME required for enterprise runners"; exit 1 )
    _SHORT_URL="https://${_GITHUB_HOST}/enterprises/${ENTERPRISE_NAME}"
    RUNNER_SCOPE="enterprise"
    ;;

  *)
    [[ -z ${REPO_URL} ]] && ( echo "REPO_URL required for repo runners"; exit 1 )
    _SHORT_URL=${REPO_URL}
    RUNNER_SCOPE="repo"
    ;;
esac
_RUNNER_NAME=${RUNNER_NAME:-${RUNNER_NAME_PREFIX:-github-runner}-$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 13 ; echo '')}
_LABELS=${LABELS:-default}
echo "Configuring"
echo "runner URL" "${_SHORT_URL}"
echo "workdir ${WORKDIR}"
echo "access token" "${ACCESS_TOKEN}"
echo "labels ${_LABELS}"
echo "runner name" "${_RUNNER_NAME}"

echo "Obtaining the token of the runner"
_TOKEN=$(ACCESS_TOKEN="${ACCESS_TOKEN}" bash /token.sh)
RUNNER_TOKEN=$(echo "${_TOKEN}" | jq -r .token)
echo "RUNNER_TOKEN ${RUNNER_TOKEN}"

gosu runner ./config.sh \
    --url "${_SHORT_URL}" \
    --token "${RUNNER_TOKEN}" \
    --name "${_RUNNER_NAME}" \
    --work "${WORKDIR}" \
    --labels "${_LABELS}" \
    --unattended \
    --replace

[[ ! -d "${WORKDIR}" ]] && mkdir "${WORKDIR}"

# exec /usr/bin/tini -g -- $@
gosu runner "$@"
