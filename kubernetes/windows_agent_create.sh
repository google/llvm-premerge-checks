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

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
ROOT_DIR="$(dirname ${DIR})"

# get config options
source "${ROOT_DIR}/k8s_config"
NAME=agent-windows-2

gcloud compute instances create ${NAME} \
    --machine-type=n1-standard-32 \
    --local-ssd=device-name=local-ssd-0 \
    --image-project=gce-uefi-images \
    --image-family=windows-2019-core-for-containers \