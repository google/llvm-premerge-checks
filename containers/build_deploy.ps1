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
$VERSION_FILE="VERSION"

# get config options
Get-Content "${ROOT_DIR}\k8s_config" | Foreach-Object{
    if (! $_.StartsWith('#') ){
        $var = $_.Split('=')
        New-Variable -Name $var[0] -Value $var[1]
    }
}

$QUALIFIED_NAME="${GCR_HOSTNAME}/${GCP_PROJECT}/${IMAGE_NAME}"

Push-Location "$PSScriptRoot\$IMAGE_NAME"
$container_version=[int](Get-Content $VERSION_FILE)
$container_version+=1
$agent_windows_version=Get-Content "../agent-windows-vs2019/$VERSION_FILE"

Write-Host "Building ${IMAGE_NAME}:${container_version}..."
Write-Host "Using windows-agent ${agent_windows_version}"

Invoke-Call -ScriptBlock {
    docker build . `
        -t ${IMAGE_NAME}:${container_version} `
        -t ${IMAGE_NAME}:latest `
        --build-arg agent_windows_version=$agent_windows_version
    }
Invoke-Call -ScriptBlock {
    docker tag ${IMAGE_NAME}:${container_version} ${QUALIFIED_NAME}:${container_version}
}
Invoke-Call -ScriptBlock {
    docker tag ${IMAGE_NAME}:latest ${QUALIFIED_NAME}:latest
}
Invoke-Call -ScriptBlock {
    docker push ${QUALIFIED_NAME}:$container_version
}
Invoke-Call -ScriptBlock {
    docker push ${QUALIFIED_NAME}:latest
}
$container_version | Out-File $VERSION_FILE
Pop-Location