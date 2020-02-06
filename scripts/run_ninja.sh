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
set -eu

# Runs ninja
# Inputs: TARGET_DIR, WORKSPACE.
# Outputs: $TARGET_DIR/test_results.xml

CMD=$1
echo "Running ninja ${CMD}... ====================================="

ulimit -n 8192
cd "${WORKSPACE}/build"

set +e
ninja ${CMD} 
RETURN_CODE="$?"
set -e

echo "ninja ${CMD} completed ======================================"
if test -f "test-results.xml" ; then
  echo "copying test_results.xml to ${TARGET_DIR}"
  # wait for file?
  sleep 10s
  du "test-results.xml"
  cp test-results.xml "${TARGET_DIR}"
  sleep 10s
fi

exit ${RETURN_CODE}