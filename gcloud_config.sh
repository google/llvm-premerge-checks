#!/bin/bash
set -uo pipefail
gcloud config set project ${GCP_PROJECT}
gcloud config set compute/zone ${GCP_ZONE}
gcloud auth configure-docker
gcloud container clusters get-credentials $GCP_CLUSTER

