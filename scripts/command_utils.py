#!/usr/bin/env python3
# Copyright 2023 Google LLC
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

import os
import sys

def get_env_or_die(name: str):
  v = os.environ.get(name)
  if not v:
    sys.stderr.write(f"Error: '{name}' environment variable is not set.\n")
    exit(2)
  return v