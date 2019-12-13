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

Set-PSDebug -Trace 1

if (Test-Path -PathType Container .git){
    Write-Output "performing git pull..."
    git checkout master 2>&1
    git reset --hard 2>&1
    git clean -fdx 2>&1
    git pull 2>&1
    # TODO: in case of errors: delete folder and clone
} else {
    Write-Output "performing git clone..."
    git clone -q --depth 1 https://github.com/llvm/llvm-project 2>&1
}