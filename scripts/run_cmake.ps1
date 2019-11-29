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

Remove-Item build -Recurse -ErrorAction Ignore
New-Item -ItemType Directory -Force -Path build | Out-Null
Push-Location build

Invoke-CmdScript "C:\Program Files (x86)\Microsoft Visual Studio\2017\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=amd64 -host_arch=amd64

Invoke-Call -ScriptBlock { 
    cmake.exe ..\llvm -G Ninja -DCMAKE_BUILD_TYPE=Release `
        -D LLVM_ENABLE_PROJECTS="clang;clang-tools-extra;libcxx;libcxxabi;lld" `
        -D LLVM_ENABLE_ASSERTIONS=ON `
        -DLLVM_LIT_ARGS="-v --xunit-xml-output test-results.xml" `
        -D LLVM_ENABLE_DIA_SDK=OFF
} -ErrorAction Stop

# LLVM_ENABLE_DIA_SDK=OFF is a workaround to make the tests pass.
# see https://bugs.llvm.org/show_bug.cgi?id=44151

Pop-Location