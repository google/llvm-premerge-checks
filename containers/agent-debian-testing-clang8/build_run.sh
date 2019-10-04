#!/bin/bash
set -eux

IMAGE_NAME="agent-debian-testing-clang8"

docker build -t ${IMAGE_NAME} .
docker run -i -t ${IMAGE_NAME}