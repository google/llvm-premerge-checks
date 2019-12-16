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
New-Variable -Name diskid -Value (Get-Disk -FriendlyName "Google PersistentDisk").Number
# TODO: check if machine has an SSD
# TODO: only do this, if SSD is not yet usable
Initialize-Disk -Number $diskid
New-Partition -DiskNumber $diskid -UseMaximumSize -AssignDriveLetter
Format-Volume -DriveLetter D

Write-Host "install chocolately as package manager..."
iex ((new-object net.webclient).DownloadString('https://chocolatey.org/install.ps1'))
choco feature disable --name showDownloadProgress
choco install git

Write-Host "Mounting result storage..."
Install-WindowsFeature NFS-Client
net use E: \\results.local\exports /PERSISTENT:YES

Set-Location D:\
git clone https://github.com/google/llvm-premerge-checks
