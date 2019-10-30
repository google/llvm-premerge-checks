# Copyright 2019 Google LLC
#
# Licensed under the the Apache License v2.0 with LLVM Exceptions (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://llvm.org/LICENSE.txt
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# define command line arguments
param(
    [Parameter(Mandatory=$true)][string]$IMAGE_NAME
)

# set script to stop on first error
$ErrorActionPreference = "Stop"

# some docs recommend setting 2GB memory limit
docker build --memory 2GB -t $IMAGE_NAME "$PSScriptRoot\$IMAGE_NAME"
If ($LastExitCode -ne 0) {
    exit
}

docker run -i -t $IMAGE_NAME
If ($LastExitCode -ne 0) {
    exit
}