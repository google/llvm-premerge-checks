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

Write-Host "Initializing local SSD..."
New-Variable -Name diskid -Value (Get-Disk -FriendlyName "Google EphemeralDisk").Number
#New-Variable -Name diskid -Value (Get-Disk -FriendlyName "NVMe nvme_card").Number

# TODO: check if machine has an SSD
# TODO: only do this, if SSD is not yet partioned and formatted
Initialize-Disk -Number $diskid
New-Partition -DiskNumber $diskid -UseMaximumSize -AssignDriveLetter
Format-Volume -DriveLetter D

Write-Host "install chocolately as package manager..."
iex ((new-object net.webclient).DownloadString('https://chocolatey.org/install.ps1'))
choco feature disable --name showDownloadProgress
choco install -y git

# move docker folder to SSD to get better IO performance
New-Item -Path "D:\" -Name "Docker" -ItemType "directory"
cmd /C "mklink /j C:\ProgramData\Docker D:\docker"

# create folder for credentials
New-Item -Path "C:\" -Name "credentials" -ItemType "directory"

# install Docker
Install-PackageProvider -Name NuGet -Force
Install-Module -Name DockerMsftProvider -Repository PSGallery -Force
Install-Package -Name docker -ProviderName DockerMsftProvider -Force
sc.exe config docker start=delayed-auto

# install gcloud and authenticate access to gcr.io registry
# TODO: find a better way to install the Google Cloud SDK, avoid ingoring the checksum
choco install -y gcloudsdk --ignore-checksums

# exclude drive d from Virus scans, to get better performance
Add-MpPreference -ExclusionPath “D:\”

# clone scripts repo (this one)
git clone https://github.com/google/llvm-premerge-checks.git "c:\llvm-premerge-checks"

# Reboot
Restart-Computer -Force
