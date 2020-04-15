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

# Starts a new instances of a docker image. Example:
# sudo build_run.sh agent-debian-testing-ssd /bin/bash

set -eux
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

IMAGE_NAME="${1%/}"

cd "${DIR}/${IMAGE_NAME}"
docker build -t ${IMAGE_NAME} .
docker run -i -t -v ~/.llvm-premerge-checks:/credentials -v ${DIR}/workspace:/workspace ${IMAGE_NAME} ${2}
