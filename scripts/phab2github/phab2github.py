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
from phab_wrapper import PhabWrapper, Revision
import subprocess

# TODO: move to config file
LLVM_GITHUB_URL = 'ssh://git@github.com/llvm/llvm-project'
_LOGGER = logging.getLogger()


class Phab2Github:

    def __init__(self, workdir: str):
        self.workdir = workdir
        self.llvm_dir = os.path.join(self.workdir, 'llvm-project')
        self.repo = None  # type: Optional[git.Repo]
        self.phab_wrapper = PhabWrapper()

    def sync(self):
        _LOGGER.info('Starting sync...')
        self._refresh_master()
        revisions = self.phab_wrapper.get_revisions()
        for revision in revisions:
            self.create_branch(revision)
            self.apply_patch(revision.latest_diff,
                             self.phab_wrapper.get_raw_patch(revision.latest_diff))

    def _refresh_master(self):
        if not os.path.exists(self.workdir):
            os.mkdir(self.workdir)
        if os.path.exists(self.llvm_dir):
            # TODO: in case of errors: delete and clone
            _LOGGER.info('pulling origin...')
            self.repo = git.Repo(self.llvm_dir)
            self.repo.remotes.origin.fetch()
        else:
            _LOGGER.info('cloning repository...')
            git.Repo.clone_from(LLVM_GITHUB_URL, self.llvm_dir)
            self.repo = git.Repo(self.llvm_dir)
        _LOGGER.info('refresh of master branch completed')

    def create_branch(self, revision: Revision):
        name = 'phab-D{}'.format(revision.id)
        if name in self.repo.heads:
            self.repo.head.reference = self.repo.heads['master']
            self.repo.head.reset(index=True, working_tree=True)
            self.repo.delete_head(name)
        base_hash = revision.latest_diff.base_hash
        if base_hash is None:
            base_hash = 'origin/master'
        _LOGGER.info('creating branch {} based one {}...'.format(name, base_hash))
        try:
            new_branch = self.repo.create_head(name, base_hash)
        except ValueError:
            # commit hash not found, try again with master
            base_hash = 'origin/master'
            new_branch = self.repo.create_head(name, base_hash)
        self.repo.head.reference = new_branch
        self.repo.head.reset(index=True, working_tree=True)

    def apply_patch(self, diff: "Diff", raw_patch: str):
        proc = subprocess.run('git apply --ignore-whitespace --whitespace=fix -', input=raw_patch, shell=True, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode != 0:
            raise Exception('Applying patch failed:\n{}'.format(proc.stdout + proc.stderr))
        self.repo.index.commit(message='applying diff Phabricator Revision {}\n\ndiff: {}'.format(diff.revision, diff.id))


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    rootdir = os.path.dirname(os.path.abspath(__file__))
    tmpdir = os.path.join(rootdir, 'tmp')
    p2g = Phab2Github(tmpdir)
    p2g.sync()
