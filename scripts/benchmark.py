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

"""Run benchmark of the various steps in the pre-merge tests.

This can be used to tune the build times.
"""

import argparse
import csv
import datetime
import os
import platform
import shutil
import subprocess
import sys
from typing import Optional, Dict, List


class Cmd:
    """Command to be executed as part of the benchmark.

    If name is not set, the results will not be logged to the result file.
    """

    def __init__(self, cmd: str, title: str = None):
        self.cmd = cmd  # type: str
        self.title = title  # type: Optional[str]
        self.execution_time = None  # type: Optional[datetime.timedelta]

    @property
    def has_title(self):
        return self.title is None


class Remove(Cmd):
    """Remove command, sensitive to OS."""

    def __init__(self, path: str):
        if platform.system() == 'Windows':
            cmd = 'cmd /c rd /s/q {}'.format(path)
        else:
            cmd = 'rm -rf {}'.format(path)
        super().__init__(cmd, "rm -rf {}".format(path))


# commands for the benchmark
COMMANDS = [
    Cmd('git clone https://github.com/llvm/llvm-project .', 'git clone'),
    Cmd('git checkout release/10.x', 'git checkout release'),
    Cmd('git checkout {commit}'),
    Cmd('git pull', 'git pull'),
    Cmd('{pmt_root_path}/scripts/run_cmake.py detect', 'cmake autotdetect'),
    Cmd('{pmt_root_path}/scripts/run_ninja.py all', 'ninja all 1st'),
    Remove('build'),
    Cmd('{pmt_root_path}/scripts/run_ninja.py all', 'ninja all 2nd'),
    Cmd('{pmt_root_path}/scripts/run_ninja.py check-all', 'ninja check-all 1st'),
    Remove('build'),
    Cmd('{pmt_root_path}/scripts/run_ninja.py check-all', 'ninja check-all 2nd'),
]


def run_benchmark(commit: str, name: str, result_file_path: str, workdir: str, pmt_root_path: str):
    """Tun the benchmark, write the results to a file."""
    print('Usingn workdir {}'.format(workdir))
    print('Using scripts from {}'.format(pmt_root_path))
    if os.path.exists(workdir):
        shutil.rmtree(workdir)
    os.makedirs(workdir)
    cmd_parameters = {
        'pmt_root_path': pmt_root_path,
        'commit': commit,
    }
    for command in COMMANDS:
        run_cmd(command, cmd_parameters, workdir)
    write_results(COMMANDS, result_file_path, name)


def write_results(commands: List[Cmd], result_file_path : str, name: str):
    fieldnames = ['name']
    fieldnames.extend(cmd.title for cmd in COMMANDS if cmd.has_title)
    exists = os.path.exists(result_file_path)
    with open(result_file_path, 'a') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, dialect=csv.excel)
        if not exists:
            writer.writeheader()
        row = {
            'name': name
        }
        for command in (cmd for cmd in commands if cmd.has_title):
            row[command.title] = command.execution_time.total_seconds()
        writer.writerow(row)
    print('Benchmark completed.')


def run_cmd(command: Cmd, cmd_parameters: Dict[str, str], workdir: str):
    """Run a single command."""
    cmdline = command.cmd.format(**cmd_parameters)
    print('Running: {}'.format(cmdline))
    start_time = datetime.datetime.now()
    proc = subprocess.Popen(cmdline, shell=True, cwd=workdir, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    if proc.poll() != 0:
        print(stdout)
        print(stderr)
        print('Benchmark failed.')
        sys.exit(1)
    end_time = datetime.datetime.now()
    command.execution_time = end_time - start_time
    print('  Execution time was: {}'.format(command.execution_time))


if __name__ == '__main__':
    pmt_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parser = argparse.ArgumentParser(
        description='Benchmark for LLVM pre-merge tests.')
    parser.add_argument('--commit', type=str, default='master', help="LLVM commit to run this benchmark on.")
    parser.add_argument('--result-file', type=str, default='pmt-benchmark.csv',
                        help="path to CSV file where to store the benchmark results")
    parser.add_argument('--workdir', type=str, default=os.path.join(os.getcwd(), 'benchmark'),
                        help='Folder to store the LLVM checkout.')
    parser.add_argument('name', type=str, nargs='?', help="name for the benchmark")
    args = parser.parse_args()
    run_benchmark(args.commit, args.name, args.result_file, args.workdir, pmt_root)
