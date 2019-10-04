#!/bin/bash
set -eux

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
ROOT_DIR="$(dirname ${DIR})"

# get config options
source "${ROOT_DIR}/k8s_config"

gcloud compute disks create jenkins-home \
    --description="storage for jenkins master" \
    --size=200GB \
    --type=pd-standard \
    --zone=${GCP_ZONE} \