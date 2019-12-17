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

# Runs clang-format
# Inputs: TARGET_DIR, WORKSPACE
# Outputs: ${TARGET_DIR}/clang-format.patch (if there are clang-format findings).
set -eux

echo "Running linters... ====================================="

cd "${WORKSPACE}"
# Let clang format apply patches --diff doesn't produces results in the format we want.
git-clang-format --style=llvm
set +e
git diff -U0 --exit-code > "${TARGET_DIR}"/clang-format.patch
STATUS="${PIPESTATUS[0]}"
set -e
# Revert changes of git-clang-format.
git checkout -- .

git diff HEAD^ | clang-tidy-diff -p1 -quiet > "${TARGET_DIR}"/clang-tidy.txt

echo "linters completed ======================================"
