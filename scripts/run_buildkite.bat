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

echo "--- CMake"
call %~dp0\run_cmake.bat
if %errorlevel% neq 0 exit /b %errorlevel%

echo "--- ninja all"
call %~dp0\run_ninja.bat all
if %errorlevel% neq 0 exit /b %errorlevel%

echo "--- ninja check-all"
call %~dp0\run_ninja.bat check-all
if %errorlevel% neq 0 exit /b %errorlevel%

echo "--- done"