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

CMD=$1
echo "Running ${CMD}... ====================================="
cd ${WORKSPACE}
# TODO: move copy operation to pipeline
BUILD_ID="${JOB_BASE_NAME}-${BUILD_NUMBER}"
TARGET_DIR="/mnt/nfs/results/${BUILD_ID}"

ulimit -n 8192
cd build

set +e
ninja ${CMD} 
RETURN_CODE="$?"
set -e

echo "check-all completed ======================================"
# TODO: move copy operation to pipeline
if test -f "test-results.xml" ; then
	cp test-results.xml ${TARGET_DIR}
fi

exit ${RETURN_CODE}