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

# 1st stage of the installation process.
# This script only needs to be run once per machine.

param (
    [switch]$ssd
)

if ($ssd) {
    Write-Host "Initializing local SSD..."
    New-Variable -Name diskid -Value (Get-Disk -FriendlyName "Google EphemeralDisk").Number
    #New-Variable -Name diskid -Value (Get-Disk -FriendlyName "NVMe nvme_card").Number

    # TODO: check if machine has an SSD
    # TODO: only do this, if SSD is not yet partioned and formatted
    Initialize-Disk -Number $diskid
    New-Partition -DiskNumber $diskid -UseMaximumSize -AssignDriveLetter
    Format-Volume -DriveLetter D
}

Write-Host "install chocolately as package manager..."
iex ((new-object net.webclient).DownloadString('https://chocolatey.org/install.ps1'))
choco feature disable --name showDownloadProgress
choco install -y git

if ($ssd) {
    # move docker folder to SSD to get better IO performance
    New-Item -Path "D:\" -Name "Docker" -ItemType "directory"
    cmd /C "mklink /j C:\ProgramData\Docker D:\docker"
}

# install Docker
# Install-PackageProvider -Name NuGet -Force
Install-Module -Name DockerMsftProvider -Repository PSGallery -Force
Install-Package -Name docker -ProviderName DockerMsftProvider -Force
sc.exe config docker start=delayed-auto

# install gcloud and authenticate access to gcr.io registry
# TODO: find a better way to install the Google Cloud SDK, avoid ingoring the checksum
choco install -y gcloudsdk --ignore-checksums

# exclude drive d from Virus scans, to get better performance
if ($sdd) {
    Add-MpPreference -ExclusionPath "D:\"
} else {
    New-Item -Path "C:\" -Name "ws" -ItemType "directory"
    Add-MpPreference -ExclusionPath "C:\ws"
}

# Clone scripts repo. Restarting in a new session to pick up profile updates. TODO: automate this.
Write-Host "please run 'git clone https://github.com/google/llvm-premerge-checks.git c:/llvm-premerge-checks' in a new shell"
pause
# create folder for credentials
New-Item -Path "C:\" -Name "credentials" -ItemType "directory"
set-content c:\credentials\buildkite-env.ps1 '# Insert API tokens and replace NAME with something meaningful.
# Mind the length of the agent name as it will be in path and might cause some tests to fail due to 260 character limit of paths.
$Env:buildkiteAgentToken = ""
$Env:BUILDKITE_AGENT_NAME= "NAME"
$Env:BUILDKITE_AGENT_TAGS = "queue=windows,image=${Env:IMAGE_DIGEST},name=NAME"
$Env:CONDUIT_TOKEN = ""'
Write-Host "Open editor to set agent options..."
Start-Process -FilePath "notepad" -Wait -Args "c:\credentials\buildkite-env.ps1"

# Add task to start agent after restart.
schtasks.exe /create /tn "Start Buildkite agent" /ru SYSTEM /SC ONSTART /DELAY 0005:00 /tr "powershell -command 'C:\llvm-premerge-checks\scripts\windows_agent_start_buildkite.ps1 -workdir c:\ws'"

# Install cloud agent to monitor https://cloud.google.com/stackdriver/docs/solutions/agents/ops-agent/installation#agent-install-latest-windows .
(New-Object Net.WebClient).DownloadFile("https://dl.google.com/cloudagents/add-google-cloud-ops-agent-repo.ps1", "${env:UserProfile}\add-google-cloud-ops-agent-repo.ps1")
Invoke-Expression "${env:UserProfile}\add-google-cloud-ops-agent-repo.ps1 -AlsoInstall"

# Reboot
Write-Host "Need to restart"
pause
Restart-Computer -Force
