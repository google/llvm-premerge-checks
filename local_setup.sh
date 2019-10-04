#!/bin/bash
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