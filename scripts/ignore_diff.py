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

import re
import sys
import pathspec


# Takes an output of git diff and removes files ignored by patten specified by ignore file.
def main():
    # FIXME: use argparse for parsing commandline parameters
    # Maybe FIXME: Replace path to file with flags for tidy/format, use paths relative to `__file__`
    argv = sys.argv[1:]
    if not argv:
        print("Please provide a path to .ignore file.")
        sys.exit(1)
    ignore = pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern,
                                          open(argv[0], 'r').readlines())
    good = True
    for line in sys.stdin:
        match = re.search(r'^diff --git a/(.*) b/(.*)$', line)
        if match:
            good = not (ignore.match_file(match.group(1)) and ignore.match_file(match.group(2)))
        if not good:
            continue
        sys.stdout.write(line)


if __name__ == "__main__":
    main()
