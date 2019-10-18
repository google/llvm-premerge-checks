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

echo "Running check-clang-format... ====================================="
cd ${WORKSPACE}
set +e
./clang/tools/clang-format/git-clang-format --diff
RETURN_CODE="${PIPESTATUS[0]}"
set -e

echo "End of check-clang-format ======================================"
exit ${RETURN_CODE}