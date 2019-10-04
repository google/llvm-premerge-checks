#!/bin/bash
set -eux

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
ROOT_DIR="$(dirname $(dirname ${DIR}))"

# get config options
source "${ROOT_DIR}/k8s_config"

IMAGE_NAME="agent-debian-testing-clang8"
QUALIFIED_NAME="${GCR_HOSTNAME}/${GCP_PROJECT}/${IMAGE_NAME}"

docker build -t ${IMAGE_NAME} .
docker tag ${IMAGE_NAME} ${QUALIFIED_NAME}
docker push ${QUALIFIED_NAME} 