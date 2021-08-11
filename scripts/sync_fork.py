#!/usr/bin/env python3
# Copyright 2021 Google LLC
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
from typing import List
import backoff
import git

"""URL of upstream LLVM repository."""
LLVM_GITHUB_URL = 'ssh://git@github.com/llvm/llvm-project'
FORK_REMOTE_URL = 'ssh://git@github.com/llvm-premerge-tests/llvm-project'


@backoff.on_exception(backoff.expo, Exception, max_tries=5, logger='', factor=3)
def sync_fork(path: str, branches: List[str]):
    if not os.path.isdir(path):
        logging.info(f'{path} does not exist, cloning repository...')
        repo = git.Repo.clone_from(FORK_REMOTE_URL, path)
    else:
        logging.info('repository exist, will reuse')
        repo = git.Repo(path)  # type: git.Repo
        repo.remote('origin').set_url(FORK_REMOTE_URL)
    os.chdir(path)
    logging.info(f'working dir {os.getcwd()}')
    logging.info(f'Syncing origin and upstream branches {branches}')
    if 'upstream' not in repo.remotes:
        repo.create_remote('upstream', url=LLVM_GITHUB_URL)
    repo.git.fetch('--all')
    for b in branches:
        logging.info(f'syncing branch {b}')
        if find_commit(repo, b) is None:
            logging.info(f'new head {b}')
            repo.create_head(b)
        h = repo.heads[b]
        h.checkout()
        repo.git.reset('--hard', f'upstream/{b}')
        repo.git.clean('-ffxdq')
        repo.git.push('origin', h)
    repo.git.push('origin', '--tags')


def find_commit(repo, rev):
    try:
        return repo.commit(rev)
    except:
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Sync LLVM fork with origina rpo.')
    parser.add_argument('--path', type=str, help='repository path', required=True)
    parser.add_argument('--branch', nargs='+', help='branch to sync (specify multiple to sync many branches)',
                        required=True)
    parser.add_argument('--log-level', type=str, default='INFO')
    args = parser.parse_args()
    logging.basicConfig(level=args.log_level, format='%(levelname)-7s %(message)s')
    sync_fork(args.path, args.branch)
