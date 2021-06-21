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
import logging
import os
import re
import subprocess
from typing import Optional
import pathspec

import ignore_diff
from buildkite_utils import annotate
from phabtalk.phabtalk import Report, Step


def run(base_commit, ignore_config, step: Optional[Step], report: Optional[Report]):
    """Apply clang-tidy and return if no issues were found."""
    if report is None:
        report = Report()  # For debugging.
    if step is None:
        step = Step()  # For debugging.
    r = subprocess.run(f'git diff -U0 --no-prefix {base_commit}', shell=True, capture_output=True)
    logging.debug(f'git diff {r}')
    diff = r.stdout.decode()
    if ignore_config is not None and os.path.exists(ignore_config):
        ignore = pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern,
                                              open(ignore_config, 'r').readlines())
        diff = ignore_diff.remove_ignored(diff.splitlines(keepends=True), open(ignore_config, 'r'))
        logging.debug(f'filtered diff: {diff}')
    else:
        ignore = pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, [])
    p = subprocess.Popen(['clang-tidy-diff', '-p0', '-quiet'], stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    step.reproduce_commands.append(f'git diff -U0 --no-prefix {base_commit} | clang-tidy-diff -p0')
    a = ''.join(diff)
    logging.info(f'clang-tidy input: {a}')
    out = p.communicate(input=a.encode())[0].decode()
    logging.debug(f'clang-tidy-diff {p}: {out}')
    # Typical finding looks like:
    # [cwd/]clang/include/clang/AST/DeclCXX.h:3058:20: error: ... [clang-diagnostic-error]
    pattern = '^([^:]*):(\\d+):(\\d+): (.*): (.*)'
    add_artifact = False
    logging.debug("cwd", os.getcwd())
    errors_count = 0
    warn_count = 0
    inline_comments = 0
    for line in out.splitlines(keepends=False):
        line = line.strip()
        line = line.replace(os.getcwd() + os.sep, '')
        logging.debug(line)
        if len(line) == 0 or line == 'No relevant changes found.':
            continue
        add_artifact = True
        match = re.search(pattern, line)
        if match:
            file_name = match.group(1)
            line_pos = match.group(2)
            char_pos = match.group(3)
            severity = match.group(4)
            text = match.group(5)
            text += '\n[[{} | not useful]] '.format(
                'https://github.com/google/llvm-premerge-checks/blob/main/docs/clang_tidy.md#warning-is-not-useful')
            if severity in ['warning', 'error']:
                if severity == 'warning':
                    warn_count += 1
                if severity == 'error':
                    errors_count += 1
                if ignore.match_file(file_name):
                    print('{} is ignored by pattern and no comment will be added'.format(file_name))
                else:
                    inline_comments += 1
                    report.add_lint({
                        'name': 'clang-tidy',
                        'severity': 'warning',
                        'code': 'clang-tidy',
                        'path': file_name,
                        'line': int(line_pos),
                        'char': int(char_pos),
                        'description': '{}: {}'.format(severity, text),
                    })
        else:
            logging.debug('does not match pattern')
    if add_artifact:
        p = 'clang-tidy.txt'
        with open(p, 'w') as f:
            f.write(out)
        report.add_artifact(os.getcwd(), p, 'clang-tidy')
    if errors_count + warn_count != 0:
        step.success = False
        url = "https://github.com/google/llvm-premerge-checks/blob/main/docs/clang_tidy.md#review-comments."
        annotate(f'clang-tidy found {errors_count} errors and {warn_count} warnings. {inline_comments} of them were '
                 f'added as review comments [why?]({url})', style='error')
    logging.debug(f'report: {report}')
    logging.debug(f'step: {step}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Runs clang-format against given diff with given commit. '
                                                 'Produces patch and attaches linter comments to a review.')
    parser.add_argument('--base', default='HEAD~1')
    parser.add_argument('--ignore-config', default=None, help='path to file with patters of files to ignore')
    parser.add_argument('--log-level', type=str, default='INFO')
    args = parser.parse_args()
    logging.basicConfig(level=args.log_level, format='%(levelname)-7s %(message)s')
    run(args.base, args.ignore_config, None, None)
