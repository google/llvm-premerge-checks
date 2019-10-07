#!/usr/bin/python3
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

import datetime
import os
import shutil

ROOT_DIR = '/mnt/nfs/results'
MAX_AGE = datetime.timedelta(days=90)
MAX_AGE_BIN = datetime.timedelta(days=3)

now = datetime.datetime.now()

for folder in [f for f in os.listdir(ROOT_DIR)]:
    fullpath = os.path.join(ROOT_DIR, folder)
    if not os.path.isdir(fullpath):
        continue
    print(fullpath)
    binpath = os.path.join(ROOT_DIR, folder, 'binaries')
    stats=os.stat('/tmp')    
    created = datetime.datetime.fromtimestamp(stats.st_mtime)
    print(created)
    if created + MAX_AGE < now:
        print("Deleting all results: {}".format(fullpath))
        shutil.rmtree(fullpath)
    elif os.path.exists(binpath) and created + MAX_AGE_BIN < now:
        print("Deleting binaries: {}".format(binpath))
        shutil.rmtree(binpath)
