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

echo "Running CMake... ======================================"
cd ${WORKSPACE}
rm -rf build || true
mkdir build
cd build
export CC=clang-8
export CXX=clang++-8
export LD=LLD

TARGET_DIR="/mnt/nfs/results/${JOB_BASE_NAME}-${BUILD_NUMBER}"
mkdir -p ${TARGET_DIR}

set +e
cmake -GNinja ../llvm -DCMAKE_BUILD_TYPE=Release -D LLVM_ENABLE_LLD=ON \
    -D LLVM_ENABLE_PROJECTS="clang;clang-tools-extra;libcxx;libcxxabi;lld" \
	-D LLVM_CCACHE_BUILD=ON -D LLVM_CCACHE_DIR="${CCACHE_PATH}" -D LLVM_CCACHE_MAXSIZE=20G \
    -D LLVM_ENABLE_ASSERTIONS=ON -DCMAKE_CXX_FLAGS=-gmlt \
    -DLLVM_LIT_ARGS="-v --xunit-xml-output ${WORKSPACE}/build/test-results.xml" 2>&1 | tee -a cmake-log.txt
RETURN_CODE="${PIPESTATUS[0]}"
set -e

cp cmake-log.txt CMakeCache.txt ${TARGET_DIR}
echo "CMake completed ======================================"
exit ${RETURN_CODE}