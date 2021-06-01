# Copyright 2021 Google LLC

# Licensed under the the Apache License v2.0 with LLVM Exceptions (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     https://llvm.org/LICENSE.txt

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Pull and start the Docker container for a Windows agent.
# To setup a Windows agent see docs/playbooks.md

param(
    [string]$version = "stable",
    [switch]$testing = $false,
    [string]$workdir = "c:\ws"
)

$NAME="agent-windows-buildkite"
$IMAGE="gcr.io/llvm-premerge-checks/${NAME}:${version}"

Write-Output "Authenticating docker..."
Write-Output "y`n" | gcloud auth configure-docker

Write-Output "Pulling new image '${IMAGE}'..."
docker pull ${IMAGE}
$DIGEST=$(docker image inspect --format "{{range .RepoDigests}}{{.}}{{end}}" $IMAGE) -replace ".*@sha256:(.{6})(.*)$","`$1"
Write-Output "Image digest ${DIGEST}"
Write-Output "Stopping old container..."
docker stop ${NAME}
docker rm ${NAME}
Write-Output "Starting container..."
if (${testing}) {
    docker run -it `
    -v ${workdir}:C:\ws `
    -v C:\credentials:C:\credentials `
    -e BUILDKITE_BUILD_PATH=C:\ws `
    -e IMAGE_DIGEST=${DIGEST} `
    ${IMAGE} powershell
} else {
    docker run -d `
    -v ${workdir}:C:\ws `
    -v C:\credentials:C:\credentials `
    -e BUILDKITE_BUILD_PATH=C:\ws `
    -e IMAGE_DIGEST=${DIGEST} `
    --name ${NAME} `
    ${IMAGE}
}
