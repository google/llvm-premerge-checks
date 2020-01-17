#!/bin/bash
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

set -eux

#folder where this script is stored.
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# dirty workarounds to reuse old scripts...
export WORKSPACE=`pwd`
export TARGET_DIR=/tmp

# create a clean build folder
BUILD_DIR=${WORKSPACE}/build
rm -rf ${BUILD_DIR} || true
mkdir -p ${BUILD_DIR}

echo "--- CMake"
${DIR}/run_cmake.sh

echo "--- ninja all"
${DIR}/run_ninja.sh all

echo "--- ninja check-all"
${DIR}/run_ninja.sh check-all

echo "--- done"