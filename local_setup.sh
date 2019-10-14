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


# Run this script once to install all required tools and configure your machine.


ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# install all the required tools for managing the cluster
sudo apt install -y google-cloud-sdk kubectl docker

# configure gCloud
source "${ROOT_DIR}/k8s_config"
gcloud config set project ${GCP_PROJECT}
gcloud config set compute/zone ${GCP_ZONE}

# setup docker for pushing containers
gcloud auth configure-docker
gcloud container clusters get-credentials $GCP_CLUSTER