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
import github
import json
import sys

# TODO: move to config file
LLVM_GITHUB_URL = 'ssh://git@github.com/llvm/llvm-project'
MY_GITHUB_URL = 'ssh://git@github.com/christiankuehnel/llvm-project'
MY_REPO = 'christiankuehnel/llvm-project'
_LOGGER = logging.getLogger()


class Phab2Github:

    def __init__(self, workdir: str):
        self.workdir = workdir
        self.llvm_dir = os.path.join(self.workdir, 'llvm-project')
        self.repo = None  # type: Optional[git.Repo]
        self.phab_wrapper = PhabWrapper()
        self.github = self._create_github()
        self.github_repo = self.github.get_repo(MY_REPO) # type: github.Repository

    def sync(self):
        _LOGGER.info('Starting sync...')
        self._refresh_master()
        revisions = self.phab_wrapper.get_revisions()
        for revision in revisions:
            try:
                self.create_branch(revision)
                self.apply_patch(revision.latest_diff,
                                 self.phab_wrapper.get_raw_patch(revision.latest_diff))
                self.repo.git.push('--force', 'origin', revision.branch_name)
                # TODO: check if pull request already exists
                self.github_repo.create_pull(title=revision.title,
                                             body=revision.summary,
                                             head=revision.branch_name,
                                             base='master')
            except Exception as e:
                _LOGGER.exception(e)

    def _refresh_master(self):
        if not os.path.exists(self.workdir):
            os.mkdir(self.workdir)
        if os.path.exists(self.llvm_dir):
            # TODO: in case of errors: delete and clone
            _LOGGER.info('pulling origin...')
            self.repo = git.Repo(self.llvm_dir)
            self.repo.git.fetch()
            self.repo.git.checkout('master')
            self.repo.git.pull('upstream', 'master')
            self.repo.git.push('origin', 'master')
        else:
            _LOGGER.info('cloning repository...')
            git.Repo.clone_from(MY_GITHUB_URL, self.llvm_dir)
            self.repo = git.Repo(self.llvm_dir)
            self.repo.create_remote('upstream', url=LLVM_GITHUB_URL)
            self.repo.remotes.upstream.fetch()
        _LOGGER.info('refresh of master branch completed')

    def create_branch(self, revision: Revision):
        name = revision.branch_name
        if name in self.repo.heads:
            self.repo.git.checkout('master')
            self.repo.git.branch('-D', name)
        base_hash = revision.latest_diff.base_hash
        if base_hash is None:
            base_hash = 'upstream/master'
        _LOGGER.info('creating branch {} based one {}...'.format(name, base_hash))
        try:
            new_branch = self.repo.create_head(name, base_hash)
        except ValueError:
            # commit hash not found, try again with master
            _LOGGER.warning('commit hash {} not found in upstream repository. '
                            'Trying master instead...'.format(name, base_hash))
            base_hash = 'upstream/master'
            new_branch = self.repo.create_head(name, base_hash)
        self.repo.head.reference = new_branch
        self.repo.head.reset(index=True, working_tree=True)

    def apply_patch(self, diff: "Diff", raw_patch: str):
        proc = subprocess.run('git apply --ignore-whitespace --whitespace=fix -', input=raw_patch, shell=True, text=True, cwd=self.repo.working_dir,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode != 0:
            raise Exception('Applying patch failed:\n{}'.format(proc.stdout + proc.stderr))
        self.repo.git.add('-A')
        self.repo.index.commit(message='applying diff Phabricator Revision {}\n\ndiff: {}'.format(diff.revision, diff.id))

    def _create_github(self) -> github.Github:
        """Create instance of Github client.

        Reads access token from a file.
        """
        with open(os.path.expanduser('~/.llvm-premerge-checks/github-token.json')) as json_file:
            token = json.load(json_file)['token']
        return github.Github(token)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    rootdir = os.path.dirname(os.path.abspath(__file__))
    tmpdir = os.path.join(rootdir, 'tmp')
    p2g = Phab2Github(tmpdir)
    p2g.sync()
