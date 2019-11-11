rem Copyright 2019 Google LLC
rem
rem Licensed under the the Apache License v2.0 with LLVM Exceptions (the "License");
rem you may not use this file except in compliance with the License.
rem You may obtain a copy of the License at
rem
rem     https://llvm.org/LICENSE.txt
rem
rem Unless required by applicable law or agreed to in writing, software
rem distributed under the License is distributed on an "AS IS" BASIS,
rem WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
rem See the License for the specific language governing permissions and
rem limitations under the License.
md build
cd build

call "C:\Program Files (x86)\Microsoft Visual Studio\2017\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=amd64 -host_arch=amd64

"C:\Program Files\CMake\bin\cmake.exe" ..\llvm -G Ninja ^
    -D LLVM_ENABLE_PROJECTS="clang;clang-tools-extra;libcxx;libcxxabi;lld" ^
    -D LLVM_ENABLE_ASSERTIONS=ON
