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

New-Variable -Name ROOT_DIR -Value (Get-Item $PSScriptRoot).Parent.FullName

# get config options
Get-Content "${ROOT_DIR}/k8s_config" | Foreach-Object{
    $var = $_.Split('=')
    New-Variable -Name $var[0] -Value $var[1]
}

New-Variable -Name QUALIFIED_NAME -Value "${GCR_HOSTNAME}/${GCP_PROJECT}/${IMAGE_NAME}"

Push-Location "$PSScriptRoot\$IMAGE_NAME"

# TODO: get current Windows version number from host via "cmd /c ver"
# to solve these issues: https://stackoverflow.com/questions/43123851/unable-to-run-cygwin-in-windows-docker-container/52273489#52273489
docker build -t $IMAGE_NAME --build-arg version=10.0.17763.1039 .
docker tag $IMAGE_NAME $QUALIFIED_NAME
docker push $QUALIFIED_NAME
Pop-Location