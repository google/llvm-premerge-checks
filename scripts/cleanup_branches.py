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

"""The script will delete old git branches."""

import argparse
import datetime
import functools
import git
import operator
import os
import re
import sys
from typing import List


def delete_old_branches(repo_path: str, max_age: datetime.datetime, branch_patterns: List[re.Pattern],
                        *, dry_run: bool = True, remote_name: str = 'origin') -> bool:
    """Deletes 'old' branches from a git repo.

    This script assumes that $repo_path contains a current checkout of the repository ot be cleaned up.
    :retrun True IFF branches could be deleted successfully.
    """
    repo = git.Repo(repo_path)
    remote = repo.remote(name=remote_name)
    repo.git.fetch('--prune')
    refs = remote.refs
    print('Found {} branches at {} in total.'.format(len(refs), remote_name))
    del_count = 0
    fail_count = 0
    if dry_run:
        print('DRY RUN. NO BRANCHES WILL BE DELETED', flush=True)
    print('Deleting: \n', flush=True)
    for reference in refs:
        committed_date = datetime.datetime.fromtimestamp(reference.commit.committed_date)
        if committed_date < max_age and _has_pattern_match(reference.name, branch_patterns):
            print(reference.name, flush=True)
            if not dry_run:
                try:
                    remote.push(refspec=':{}'.format(reference.remote_head))
                    del_count += 1
                except git.GitCommandError as err:
                    print('ERROR: Failed to delete "{}": {}'.format(reference.name, err), flush=True)
                    fail_count += 1
    print('Deleted {} branches.'.format(del_count))
    if fail_count > 0:
        print('Failed to delete {} branches.'.format(fail_count))
    return fail_count == 0


def _has_pattern_match(name: str, patterns) -> bool:
    """Check if name matches any of the patterns"""
    return functools.reduce(
        operator.or_,
        map(lambda r: r.search(name) is not None, patterns),
        False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Clean a git repository')
    parser.add_argument('repo_path', type=str, nargs='?', default=os.getcwd())
    parser.add_argument('--days', type=int, default=30)
    parser.add_argument('--pattern', action='append', type=str)
    parser.add_argument('--dryrun', action='store_true')
    args = parser.parse_args()

    max_age = datetime.datetime.now() - datetime.timedelta(days=args.days)
    branch_pattern = [re.compile(r) for r in args.pattern]

    success = delete_old_branches(args.repo_path, max_age, branch_pattern, dry_run=args.dryrun)

    if not success:
        sys.exit(1)
