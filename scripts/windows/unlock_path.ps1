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

# Based ob https://dandraka.com/2019/08/13/find-and-kill-processes-that-lock-a-file-or-directory/
$path = $args[0]
$handleOutput = & handle -a $path
Write-Host "Unlocking path" $path
if ($handleOutput -match "no matching handles found") {
    Write-Host "Nothing to kill, exiting"
    exit
}
$pidList = New-Object System.Collections.ArrayList
$lines = $handleOutput -split "`n"
foreach($line in $lines) {
  # sample line:
  # chrome.exe         pid: 11392  type: File           5BC: C:\Windows\Fonts\timesbd.ttf
  # regex to get pid and process name: (.*)\b(?:.*)(?:pid: )(\d*)
  $matches = $null
  $line -match "(.*)\b(?:.*)(?:pid: )(\d*)" | Out-Null
  if (-not $matches) { continue }
  if ($matches.Count -eq 0) { continue }
  $pidName = $matches[1]
  $pidStr = $matches[2]
  if ($pidList -notcontains $pidStr) {
    Write-Host "Will kill process $pidStr $pidName"
    $pidList.Add($pidStr) | Out-Null
  }
}

foreach($pidStr in $pidList) {
    $pidInt = [int]::Parse($pidStr)
    Stop-Process -Id $pidInt -Force
    Write-Host "Killed process $pidInt"
}

Write-Host "Finished"