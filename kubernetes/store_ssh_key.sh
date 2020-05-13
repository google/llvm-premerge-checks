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
set -eux

# This scripts creates a new ssh keypair (if it does not exist) and uploads
# it to a kubernetes secret.
#
# You need to manually upload the public key to Github so that you can use
# it for authentication.


LOCAL_SSH_DIR="$HOME/.llvm-premerge-checks/github-ssh"

if [ ! -d "$LOCAL_SSH_DIR" ]; then
  mkdir -p "$LOCAL_SSH_DIR"
  pushd "$LOCAL_SSH_DIR"
  ssh-keygen -b 4096 -t rsa -f "$LOCAL_SSH_DIR/id_rsa" -q -N ""
  popd
fi

kubectl create secret generic github-ssh-key --namespace jenkins \
  --from-file "$LOCAL_SSH_DIR/id_rsa" \
  --from-file "$LOCAL_SSH_DIR/id_rsa.pub"