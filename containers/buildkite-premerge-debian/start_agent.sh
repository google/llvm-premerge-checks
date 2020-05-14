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

# Buildkite installation creates 'buildkite-agent' user.
USER=buildkite-agent

# prepare work directory
mkdir -p "${BUILDKITE_BUILD_PATH}"
chown -R ${USER}:${USER} "${BUILDKITE_BUILD_PATH}"

export CCACHE_PATH="${BUILDKITE_BUILD_PATH}"/ccache
mkdir -p "${CCACHE_PATH}"
chown -R ${USER}:${USER} "${CCACHE_PATH}"

# /mnt/ssh should contain known_hosts, id_rsa and id_rsa.pub .
mkdir -p /var/lib/buildkite-agent/.ssh
cp /mnt/ssh/* /var/lib/buildkite-agent/.ssh
chmod 700 /var/lib/buildkite-agent/.ssh
chmod 600 /var/lib/buildkite-agent/.ssh/*
chown -R $USER:$USER /var/lib/buildkite-agent/.ssh

su buildkite-agent -c "buildkite-agent start"