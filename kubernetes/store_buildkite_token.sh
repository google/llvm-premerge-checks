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
#-------------------------------------------------------------------------------

# store the buildkite token as kubernetes secret
# 
# Get the token from the website [1] and store it in this file locally in
# ~/.llvm-premerge-checks/buildkite-token  
# Do not share this token with anyone!
# [1] https://buildkite.com/organizations/llvm-project/agents

kubectl create secret generic buildkite-token --namespace jenkins --from-file ~/.llvm-premerge-checks/buildkite-token 