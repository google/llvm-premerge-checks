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
if (( $# != 2 )); then
  echo "Syntax: lint.sh <COMMIT> <OUTPUT_DIR>"
  exit 1
fi;
# Commit to diff against
COMMIT="$1"
# output directory for test results
OUTPUT_DIR="$2"
# root directory, where the config files are located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

if [ ! -f "compile_commands.json" ] ; then
  echo "Could not find compile commands.json in $(pwd)"
  exit 1
fi

# clang-format
# Let clang format apply patches --diff doesn't produces results in the format we want.
git-clang-format "${COMMIT}"
set +e
git diff -U0 --exit-code --no-prefix | "${DIR}/ignore_diff.py" "${DIR}/clang-format.ignore" > "${OUTPUT_DIR}"/clang-format.patch
set -e
# Revert changes of git-clang-format.
git checkout -- .

# clang-tidy
git diff -U0 --no-prefix "${COMMIT}" | "${DIR}/ignore_diff.py" "${DIR}/clang-tidy.ignore" | clang-tidy-diff -p0 -quiet | sed "/^[[:space:]]*$/d" > "${OUTPUT_DIR}"/clang-tidy.txt

echo "linters completed ======================================"
