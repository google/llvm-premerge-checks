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

# Invoked at startup of windows machine. This indirection allows to simply
# restart a machine and it will pick up all script changes and will use the
# latest stable image.

param(
    [string]$version = "stable",
    [string]$workdir = "c:\ws"
)

cd c:\llvm-premerge-checks
git pull
c:\llvm-premerge-checks\scripts\windows\start_container.ps1 -version $version -workdir $workdir
