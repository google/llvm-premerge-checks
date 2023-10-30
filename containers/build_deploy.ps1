# Copyright 2019 Google LLC

# Licensed under the the Apache License v2.0 with LLVM Exceptions (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     https://llvm.org/LICENSE.txt

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# define command line arguments
param(
    [Parameter(Mandatory=$true)][string]$IMAGE_NAME
)

$ROOT_DIR=(Get-Item $PSScriptRoot).Parent.FullName
. ${ROOT_DIR}\scripts\common.ps1

$QUALIFIED_NAME="gcr.io/llvm-premerge-checks/${IMAGE_NAME}"

Push-Location "$PSScriptRoot\$IMAGE_NAME"

Write-Host "Building ${IMAGE_NAME}..."

Invoke-Call -ScriptBlock {
    docker build . -t ${IMAGE_NAME}:latest
}
Invoke-Call -ScriptBlock {
    docker tag ${IMAGE_NAME}:latest ${QUALIFIED_NAME}:latest
}
Invoke-Call -ScriptBlock {
    docker push ${QUALIFIED_NAME}:latest
}
Pop-Location