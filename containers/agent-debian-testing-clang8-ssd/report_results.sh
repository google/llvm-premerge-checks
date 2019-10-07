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

SUCCESS="$1"
DIFF_ID="$2"
BUILD_ID="$3"
URL="https://reviews.llvm.org"

if [ "${SUCCESS}" == "0" ]
then
    MSG="SUCCESSFUL"
else
    MSG="FAILED"
fi

arc --conduit-uri=${URL} call-conduit differential.revision.edit <<EOF
{
    "transactions": [{
        "type": "comment",
        "value": "check-all ${MSG}! \n[cmake.log](http://results.llvm-merge-guard.org/${BUILD_ID}/cmake.log)\n[ninja_check_all.log](http://results.llvm-merge-guard.org/${BUILD_ID}/ninja_check_all.log)"
    }],
    "objectIdentifier":"${DIFF_ID}"
}
EOF