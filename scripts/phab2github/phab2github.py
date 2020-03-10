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

import os
from typing import Optional
import git
import logging

# TODO: move to config file
LLVM_GITHUB_URL = 'ssh://git@github.com/llvm/llvm-project'
_LOGGER = logging.getLogger()


class Phab2Github:

    def __init__(self, workdir: str):
        self.workdir = workdir
        self.llvm_dir = os.path.join(self.workdir, 'llvm-project')
        self.repo = None  # type: Optional[git.Repo]

    def sync(self):
        _LOGGER.info('Starting sync...')
        self._refresh_master()
        revisions = self._get_revisions()

    def _refresh_master(self):
        if not os.path.exists(self.workdir):
            os.mkdir(self.workdir)
        if os.path.exists(self.llvm_dir):
            # TODO: in case of errors: delete and clone
            _LOGGER.info('pulling origin...')
            self.repo = git.Repo(self.llvm_dir)
            self.repo.remotes.origin.pull()
        else:
            _LOGGER.info('cloning repository...')
            git.Repo.clone_from(LLVM_GITHUB_URL, self.llvm_dir)
        _LOGGER.info('refresh of master branch completed')


if __name__ == '__main__':
    rootdir = os.path.dirname(os.path.abspath(__file__))
    tmpdir = os.path.join(rootdir, 'tmp')
    p2g = Phab2Github(tmpdir)
    p2g.sync()
