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

Write-Host "Initializing local SSD..."
New-Variable -Name diskid -Value (Get-Disk -FriendlyName "NVMe nvme_card").Number
# TODO: check if machine has an SSD
# TODO: only do this, if SSD is not yet usable
Initialize-Disk -Number $diskid
New-Partition -DiskNumber $diskid -UseMaximumSize -AssignDriveLetter
Format-Volume -DriveLetter D

Write-Host "install chocolately as package manager..."
iex ((new-object net.webclient).DownloadString('https://chocolatey.org/install.ps1')) ; `
choco feature disable --name showDownloadProgress

Write-Host "Installing Visual Studio build tools..."
choco install visualcpp-build-tools `
        --version 15.0.26228.20170424 -y --params "'/IncludeOptional'" ;`
Write-Host 'Waiting for Visual C++ Build Tools to finish'; `
Wait-Process -Name vs_installer

Write-Host "Installing misc tools"
# install other tools as described in https://llvm.org/docs/GettingStartedVS.html
# and a few more that were not documented...
choco install -y git python2 ninja gnuwin cmake
pip install psutil    

Write-Host "Setting environment variables..."
$Env:PYTHONIOENCODING=UTF-8
$Env:path = $Env:path + ';c:\Program Files (x86)\GnuWin32\bin;C:\Program Files\CMake\bin'

# support long file names during git checkout
Write-Host "Setting git config..."
git config --system core.longpaths true
git config --global core.autocrlf false

# Above: genric LLVM-related things
#-------------
# Below: Jenkins specific things

Write-Host "Installing openjdk..."
RUN choco install -y openjdk

Write-Host "Installing Jenkins swarm agent..."
$SWARM_PLUGIN_URL="https://repo.jenkins-ci.org/releases/org/jenkins-ci/plugins/swarm-client/3.17/swarm-client-3.17.jar"
$SWARM_PLUGIN_JAR="C:\jenkins\swarm-client.jar"
mkdir c:\jenkins
Invoke-WebRequest -Uri $SWARM_PLUGIN_URL -OutFile $SWARM_PLUGIN_JAR


Write-Host "Mounting result storage..."
Install-WindowsFeature NFS-Client
net use E: \\results.local\exports

