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

def run_ninja(target: str, repo_path: str):   
    build_dir = os.path.join(repo_path, 'build')

    if 'SCCACHE_DIR' in os.environ:
        # FIXME: Is there a more elegant way to find out if sccache server
        #        is already running?
        try:
            # start the server with VS environment configured
            _run_cmd('sccache --start-server')
        except subprocess.CalledProcessError:
            print('sccache already running, not starting a new one.')

    cmd = 'ninja {}'.format(target)
    _run_cmd(cmd, cwd=build_dir)


def _run_cmd(cmd: str, *, cwd: str = None):
    # On Windows: configure Visutal Studio before running ninja
    if platform.system() == 'Windows':
        # FIXME: move this path to a config file
        cmd = r'"C:\Program Files (x86)\Microsoft Visual Studio\2017\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=amd64 -host_arch=amd64 && ' + cmd

    subprocess.check_call(cmd, shell=True, cwd=cwd)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run ninja for LLVM.')
    parser.add_argument('target')
    parser.add_argument('repo_path', type=str, nargs='?', default=os.getcwd())
    args = parser.parse_args()
    run_ninja(args.target, args.repo_path)
