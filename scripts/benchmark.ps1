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

param(
    [Parameter(Mandatory=$true)][string]$WORKDIR
)

Measure-Command { git clone --depth 1 https://github.com/llvm/llvm-project $WORKDIR }

Set-Location $WORKDIR
Measure-Command {& $PSScriptRoot\run_cmake.ps1}
Measure-Command {& $PSScriptRoot\run_ninja.ps1 all}
Measure-Command {& $PSScriptRoot\run_ninja.ps1 check-all}
