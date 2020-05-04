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

import argparse
import os
import platform
import subprocess


def run_ninja(target: str, repo_path: str, *, dryrun:bool = False):
    build_dir = os.path.join(repo_path, 'build')
    cmd = 'ninja {}'.format(target)
    if dryrun:
        print('Dryrun. Command would have been:\n{}'.format(cmd))
    else:
        subprocess.check_call(cmd, shell=True, cwd=build_dir)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run ninja for LLVM.')
    parser.add_argument('target')
    parser.add_argument('repo_path', type=str, nargs='?', default=os.getcwd())
    parser.add_argument('--dryrun', action='store_true')
    args = parser.parse_args()
    run_ninja(args.target, args.repo_path, dryrun=args.dryrun)
