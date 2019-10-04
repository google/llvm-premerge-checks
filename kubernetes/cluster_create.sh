#!/bin/bash
set -eux

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
ROOT_DIR="$(dirname ${DIR})"

# get config options
source "${ROOT_DIR}/k8s_config"

# create the cluster
gcloud container clusters create $GCP_CLUSTER --zone $GCP_ZONE \
    --machine-type=n1-standard-32 --num-nodes=1
