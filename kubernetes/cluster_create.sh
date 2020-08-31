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

# create the cluster
gcloud container clusters create $GCP_CLUSTER --zone $GCP_ZONE \
    --machine-type=n1-standard-4 --num-nodes=1

# Linux agents node pool with local ssd.
# https://cloud.google.com/kubernetes-engine/docs/how-to/persistent-volumes/local-ssd
gcloud container node-pools create linux-agents --cluster $GCP_CLUSTER --zone $GCP_ZONE \
    --machine-type=n1-standard-32 --num-nodes=2 --local-ssd-count=1

# created separate cluster for windows, as we need "ip-alias" enabled
# this can't be changed in a running cluster...
gcloud beta container clusters create $GCP_CLUSTER_WINDOWS \
  --enable-ip-alias \
  --num-nodes=1 \
  --release-channel=rapid \
  --enable-private-nodes

# Windows agents with local ssd
gcloud container node-pools create windows-pool --cluster $GCP_CLUSTER_WINDOWS \
    --image-type=WINDOWS_SAC --no-enable-autoupgrade \
    --machine-type=n1-standard-16 --local-ssd-count=1

# create static IP address
# IP can be created, but not used in Ingress. Not sure why
gcloud compute addresses create web-static-ip --zone=$GCP_ZONE