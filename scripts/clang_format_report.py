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
import subprocess
import logging

import pathspec
import unidiff

from typing import Tuple, Optional
from phabtalk.phabtalk import Report, CheckResult


def get_diff(base_commit) -> Tuple[bool, str]:
    r = subprocess.run(f'git-clang-format {base_commit}', shell=True)
    logging.debug(f'git-clang-format {r}')
    if r.returncode != 0:
        logging.error(f'git-clang-format returned an non-zero exit code {r.returncode}')
        r = subprocess.run(f'git checkout -- .', stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        logging.debug(f'git reset {r}')
        return False, ''
    diff_run = subprocess.run(f'git diff -U0 --no-prefix --exit-code', capture_output=True, shell=True)
    logging.debug(f'git diff {diff_run}')
    r = subprocess.run(f'git checkout -- .', stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    logging.debug(f'git reset {r}')
    return True, diff_run.stdout.decode()


def run(base_commit, ignore_config, report: Optional[Report]):
    """Apply clang-format and return if no issues were found."""
    if report is None:
        report = Report()  # For debugging.
    r, patch = get_diff(base_commit)
    if not r:
        report.add_step('clang-format', CheckResult.FAILURE, '')
        return
    add_artifact = False
    patches = unidiff.PatchSet(patch)
    ignore_lines = []
    if ignore_config is not None and os.path.exists(ignore_config):
        ignore_lines = open(ignore_config, 'r').readlines()
    ignore = pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, ignore_lines)
    patched_file: unidiff.PatchedFile
    success = True
    for patched_file in patches:
        add_artifact = True
        if ignore.match_file(patched_file.source_file) or ignore.match_file(patched_file.target_file):
            logging.info(f'patch of {patched_file.patch_info} is ignored')
            continue
        hunk: unidiff.Hunk
        for hunk in patched_file:
            lines = [str(x) for x in hunk]
            success = False
            m = 10  # max number of lines to report.
            description = 'please reformat the code\n```\n'
            n = len(lines)
            cut = n > m + 1
            if cut:
                lines = lines[:m]
            description += ''.join(lines) + '\n```'
            if cut:
                description += f'\n{n - m} diff lines are omitted. See full path.'
            report.add_lint({
                'name': 'clang-format',
                'severity': 'autofix',
                'code': 'clang-format',
                'path': patched_file.source_file,
                'line': hunk.source_start,
                'char': 1,
                'description': description,
            })
    if add_artifact:
        patch_file = 'clang-format.patch'
        with open(patch_file, 'w') as f:
            f.write(patch)
        report.add_artifact(os.getcwd(), patch_file, 'clang-format')
    if success:
        report.add_step('clang-format', CheckResult.SUCCESS, message='')
    else:
        report.add_step(
            'clang-format',
            CheckResult.FAILURE,
            'Please format your changes with clang-format by running `git-clang-format HEAD^` or applying patch.')
    logging.debug(f'report: {report}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Runs clang-format against given diff with given commit. '
                                                 'Produces patch and attaches linter comments to a review.')
    parser.add_argument('--base', default='HEAD~1')
    parser.add_argument('--ignore-config', default=None, help='path to file with patters of files to ignore')
    parser.add_argument('--log-level', type=str, default='INFO')
    args = parser.parse_args()
    logging.basicConfig(level=args.log_level)
    run(args.base, args.ignore_config, None)
