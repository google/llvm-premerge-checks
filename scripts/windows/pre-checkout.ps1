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

echo "BUILDKITE_BUILD_CHECKOUT_PATH: $env:BUILDKITE_BUILD_CHECKOUT_PATH"
echo "unlocking git"
taskkill /F /IM git.exe
rm -Force "$env:BUILDKITE_BUILD_CHECKOUT_PATH/.git/index.lock"
echo "BUILDKITE_BUILD_PATH: $env:BUILDKITE_BUILD_PATH"
echo 'running processes (before)'
Get-Process | Where-Object {$_.Path -like "$env:BUILDKITE_BUILD_PATH*"} | Select-Object -ExpandProperty Path
echo "unlocking $env:BUILDKITE_BUILD_PATH"
handle -nobanner $env:BUILDKITE_BUILD_CHECKOUT_PATH
c:\llvm-premerge-checks\scripts\windows\unlock_path.ps1 $env:BUILDKITE_BUILD_CHECKOUT_PATH
echo 'running processes (after)'
Get-Process | Where-Object {$_.Path -like "$env:BUILDKITE_BUILD_PATH*"} | Select-Object -ExpandProperty Path
