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

. ${PSScriptRoot}\common.ps1

Write-Host "Installing Visual Studio build tools..."
choco install -y visualcpp-build-tools --version 15.0.26228.20170424 -y --params "'/IncludeOptional'"
Write-Host 'Waiting for Visual C++ Build Tools to finish'
Wait-Process -Name vs_installer

Write-Host "Installing misc tools"
# install other tools as described in https://llvm.org/docs/GettingStartedVS.html
# and a few more that were not documented...
choco install -y git python2 ninja gnuwin cmake
pip install psutil

Write-Host "Setting environment variables..."
[System.Environment]::SetEnvironmentVariable('PYTHONIOENCODING', 'UTF-8', [System.EnvironmentVariableTarget]::User)
$oldpath=[System.Environment]::GetEnvironmentVariable('path',[System.EnvironmentVariableTarget]::User)
[System.Environment]::SetEnvironmentVariable('path', $oldpath + 'c:\Program Files (x86)\GnuWin32\bin;C:\Program Files\CMake\bin', [System.EnvironmentVariableTarget]::User)
# support long file names during git checkout
Write-Host "Setting git config..."
git config --system core.longpaths true
git config --global core.autocrlf false

# Above: genric LLVM-related things
#-------------
# Below: Jenkins specific things

Write-Host "Installing openjdk..."
choco install -y openjdk

Write-Host "Installing Jenkins swarm agent..."
$SWARM_PLUGIN_URL="https://repo.jenkins-ci.org/releases/org/jenkins-ci/plugins/swarm-client/3.17/swarm-client-3.17.jar"
$SWARM_PLUGIN_JAR="C:\jenkins\swarm-client.jar"
mkdir c:\jenkins
Invoke-WebRequest -Uri $SWARM_PLUGIN_URL -OutFile $SWARM_PLUGIN_JAR
