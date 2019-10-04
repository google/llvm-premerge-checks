#!/bin/bash
set -eux

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
ROOT_DIR="$(dirname ${DIR})"

# get config options
source "${ROOT_DIR}/k8s_config"

#TODO: check gcloud auth login

# create the cluster
gcloud container clusters delete $GCP_CLUSTER