#!/bin/bash
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
#-------------------------------------------------------------------------------
# set up Google Cloud Storage for the build results

set -eux

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
ROOT_DIR="$(dirname ${DIR})"

# get config options
source "${ROOT_DIR}/k8s_config"

# create a bucket
gsutil mb --retention 90d gs://${GCS_BUCKET}

# put a dummy file there so we can set the path ACLs
echo "hello world" | gsutil cp - gs://${GCS_BUCKET}/results/hello.txt

# make results folder world-readable, now files are accessable via
# https://storage.googleapis.com/llvm-premerge-checks/results/
gsutil iam ch allUsers:objectViewer gs://${GCS_BUCKET}
gsutil acl ch -u AllUsers:R gs://${GCS_BUCKET}/results/*

AGENT_SERVICE_ACCOUNT="build-agent-results"
KEY_FILE="${AGENT_SERVICE_ACCOUNT}_key.json"

# create service account and key
gcloud iam service-accounts create ${AGENT_SERVICE_ACCOUNT} \
    --description "account for build agent to upload build results"
gcloud iam service-accounts keys create ${KEY_FILE} \
   --iam-account "${AGENT_SERVICE_ACCOUNT}@${GCP_PROJECT}.iam.gserviceaccount.com"

# upload the key to the kubernetes secret storage
kubectl create secret generic "${AGENT_SERVICE_ACCOUNT}" \
  --from-file ${KEY_FILE}

# give write permissions to service account
gsutil acl ch \
    -u "${AGENT_SERVICE_ACCOUNT}@${GCP_PROJECT}.iam.gserviceaccount.com":WRITER \
    gs://${GCS_BUCKET}
