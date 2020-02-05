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

. ${PSScriptRoot}\common.ps1

Write-Output "--- CMake"
& "${PSScriptRoot}\run_cmake.ps1" 

Write-Output "--- ninja all"
& "${PSScriptRoot}\run_ninja.ps1" all

Write-Output "--- ninja check-all"
& "${PSScriptRoot}\run_ninja.ps1" check-all

Write-Output "--- done"