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
import re
import sys
import pathspec


def remove_ignored(diff_lines, ignore_patterns_lines):
    logging.debug(f'ignore pattern {ignore_patterns_lines}')
    ignore = pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, ignore_patterns_lines)
    good = True
    result = []
    for line in diff_lines:
        match = re.search(r'^diff --git (.*) (.*)$', line)
        if match:
            good = not (ignore.match_file(match.group(1)) and ignore.match_file(match.group(2)))
        if not good:
            logging.debug(f'skip {line.rstrip()}')
            continue
        result.append(line)
    return result


if __name__ == "__main__":
    # Maybe FIXME: Replace this tool usage with flags for tidy/format, use paths relative to `__file__`
    parser = argparse.ArgumentParser(description='Takes an output of git diff and removes files ignored by patten '
                                                 'specified by ignore file')
    parser.add_argument('ignore_config', default=None,
                        help='path to file with patters of files to ignore')
    parser.add_argument('--log-level', type=str, default='WARNING')
    args = parser.parse_args()
    logging.basicConfig(level=args.log_level)
    filtered = remove_ignored([x for x in sys.stdin], open(args.ignore_config, 'r').readlines())
    for x in filtered:
        sys.stdout.write(x)
