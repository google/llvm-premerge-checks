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

param (
  [Parameter(Mandatory=$false)][string]$projects="default"
)

. ${PSScriptRoot}\common.ps1

# set LLVM_ENABLE_PROJECTS to default value
# if -DetectProjects is set the projects are detected based on the files
# that were modified in the working copy
if ($projects -eq "default") {
  # These are the default projects for windows
  $LLVM_ENABLE_PROJECTS="clang;clang-tools-extra;libcxx;libc;lld;mlir;compiler-rt;libcxxabi"
} elseif ($projects -eq "detect") {
  $LLVM_ENABLE_PROJECTS = (git diff | python ${PSScriptRoot}\choose_projects.py . ) | Out-String
  $LLVM_ENABLE_PROJECTS = $LLVM_ENABLE_PROJECTS.replace("`n","").replace("`r","")
  if ($LLVM_ENABLE_PROJECTS -eq "") {
    Write-Error "Error detecting the affected projects."
    exit 1
  }
} else {
  $LLVM_ENABLE_PROJECTS=$projects
}

Write-Output "Setting LLVM_ENABLE_PROJECTS=${LLVM_ENABLE_PROJECTS}"

# Delete and re-create build folder
Remove-Item build -Recurse -ErrorAction Ignore
New-Item -ItemType Directory -Force -Path build | Out-Null
Push-Location build

# load Vistual Studio environment variables
Invoke-CmdScript "C:\Program Files (x86)\Microsoft Visual Studio\2017\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=amd64 -host_arch=amd64

# Make sure we're using the Vistual Studio compiler and linker
$env:CC="cl"
$env:CXX="cl"
$env:LD="link"

# call CMake
$ErrorActionPreference="Continue"
Invoke-Call -ScriptBlock {
  cmake ..\llvm -G Ninja -DCMAKE_BUILD_TYPE=Release  `
         -D LLVM_ENABLE_PROJECTS="${LLVM_ENABLE_PROJECTS}" `
         -D LLVM_ENABLE_ASSERTIONS=ON `
         -DLLVM_LIT_ARGS="-v --xunit-xml-output test-results.xml" `
         -D LLVM_ENABLE_DIA_SDK=OFF
}

# LLVM_ENABLE_DIA_SDK=OFF is a workaround to make the tests pass.
# see https://bugs.llvm.org/show_bug.cgi?id=44151

Pop-Location