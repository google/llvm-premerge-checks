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
import shutil
import subprocess
import sys


def check_sccache(dryrun: bool):
    """check if sccache can be started

    Wipe local cache folder if it fails with a timeout.
    This is based on the problem described here:
    https://github.com/google/llvm-premerge-checks/wiki/LLVM-pre-merge-tests-operations-blog#2020-05-04
    """
    if platform.system() != 'Windows':
        return
    if 'SCCACHE_DIR' not in os.environ:
        return
    sccache_dir = os.environ['SCCACHE_DIR']
    result = subprocess.run('sccache --start-server', shell=True, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True)
    if result.returncode == 0:
        return
    if result.stderr is not None and 'Timed out waiting for server startup' in result.stderr:
        print('sccache failed with timeout. Wiping local cache dir {}'.format(sccache_dir))
        if dryrun:
            print('Dryrun. Not deleting anything.')
        else:
            shutil.rmtree(sccache_dir)


def run_ninja(target: str, work_dir: str, *, dryrun: bool = False):
    check_sccache(dryrun)
    cmd = 'ninja {}'.format(target)
    if dryrun:
        print('Dryrun. Command would have been:\n{}'.format(cmd))
        return 0
    else:
        return subprocess.call(cmd, shell=True, cwd=work_dir)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run ninja for LLVM.')
    parser.add_argument('target')
    parser.add_argument('repo_path', type=str, nargs='?', default=os.getcwd())
    parser.add_argument('--dryrun', action='store_true')
    args = parser.parse_args()
    sys.exit(run_ninja(args.target, os.path.join(args.repo_path, 'build'), dryrun=args.dryrun))
