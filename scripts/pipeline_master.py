#!/usr/bin/env python3
# Copyright 2020 Google LLC
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

from steps import generic_linux, generic_windows, from_shell_output
import yaml

steps_generators = [
    '${BUILDKITE_BUILD_CHECKOUT_PATH}/libcxx/utils/ci/buildkite-pipeline-snapshot.sh',
]

if __name__ == '__main__':
    scripts_refspec = os.getenv("ph_scripts_refspec", "master")
    no_cache = os.getenv('ph_no_cache') is not None
    filter_output = '--filter-output' if os.getenv('ph_no_filter_output') is None else ''
    projects = os.getenv('ph_projects', 'clang;clang-tools-extra;libc;libcxx;libcxxabi;lld;libunwind;mlir;openmp;polly')
    log_level = os.getenv('ph_log_level', 'WARNING')
    notify_emails = list(filter(None, os.getenv('ph_notify_emails', '').split(',')))
    steps = []
    steps.extend(generic_linux(
        os.getenv('ph_projects', 'clang;clang-tools-extra;libc;libcxx;libcxxabi;lld;libunwind;mlir;openmp;polly'),
        False))
    # FIXME: openmp is removed as it constantly fails.

    # TODO: Make this project list be evaluated through "choose_projects"(? as now we define "all" and exclusions in
    #  two placess).
    steps.extend(generic_windows(
        os.getenv('ph_projects', 'clang;clang-tools-extra;libc;libcxx;libcxxabi;lld;libunwind;mlir;polly')))

    for gen in steps_generators:
        steps.extend(from_shell_output(gen))

    notify = []
    for e in notify_emails:
        notify.append({'email': e})
    print(yaml.dump({'steps': steps, 'notify': notify}))
