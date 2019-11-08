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
set -eux

USER_NAME="${1}"
AUTH_FILE="${HOME}/.llvm-premerge-checks/auth"

if [ -f "${AUTH_FILE}" ] ; then
    htpasswd "${AUTH_FILE}" "${USER_NAME}"
else
    mkdir -p "$(dirname "${AUTH_FILE}")"
    htpasswd -c "${AUTH_FILE}" "${USER_NAME}"
fi