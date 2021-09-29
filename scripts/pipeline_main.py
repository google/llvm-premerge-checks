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

# Script runs in checked out llvm-project directory.

import os

from steps import generic_linux, generic_windows, from_shell_output, extend_steps_env, bazel
from sync_fork import sync_fork
import git
import yaml

steps_generators = [
    '${BUILDKITE_BUILD_CHECKOUT_PATH}/libcxx/utils/ci/buildkite-pipeline-snapshot.sh',
]

if __name__ == '__main__':
    scripts_refspec = os.getenv("ph_scripts_refspec", "main")
    no_cache = os.getenv('ph_no_cache') is not None
    log_level = os.getenv('ph_log_level', 'WARNING')
    notify_emails = list(filter(None, os.getenv('ph_notify_emails', '').split(',')))
    # Syncing LLVM fork so any pipelines started from upstream llvm-project#
    # but then triggered a build on fork will observe the commit.
    sync_fork(os.path.join(os.getenv('BUILDKITE_BUILD_PATH'), 'llvm-project-fork'), [os.getenv('BUILDKITE_BRANCH'), 'main'])
    steps = []

    env = {}
    for e in os.environ:
        if e.startswith('ph_'):
            env[e] = os.getenv(e)
    repo = git.Repo('.')
    steps.extend(generic_linux(
        os.getenv('ph_projects', 'llvm;clang;clang-tools-extra;libc;libcxx;libcxxabi;lld;libunwind;mlir;openmp;polly;flang'),
        False))
    # FIXME: openmp is removed as it constantly fails.

    # TODO: Make this project list be evaluated through "choose_projects"(? as now we define "all" and exclusions in
    #  two placess).
    steps.extend(generic_windows(
        os.getenv('ph_projects', 'llvm;clang;clang-tools-extra;libc;lld;mlir;polly;flang')))
    steps.extend(bazel([], force=True))
    if os.getenv('ph_skip_generated') is None:
        e = os.environ.copy()
        # BUILDKITE_COMMIT might be an alias, e.g. "HEAD". Resolve it to make the build hermetic.
        if ('BUILDKITE_COMMIT' not in env) or (env['BUILDKITE_COMMIT'] == "HEAD"):
            env['BUILDKITE_COMMIT'] = repo.head.commit.hexsha
        for gen in steps_generators:
            steps.extend(from_shell_output(gen, env=e))

    notify = []
    for e in notify_emails:
        notify.append({'email': e})
    extend_steps_env(steps, env)
    print(yaml.dump({'steps': steps, 'notify': notify}))
