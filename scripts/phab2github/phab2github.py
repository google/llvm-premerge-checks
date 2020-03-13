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
from typing import Optional, Union
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


class ApplyPatchException(Exception):
    """A patch could not be applied."""
    pass


class Phab2Github:

    def __init__(self, workdir: str):
        self.workdir = workdir
        self.llvm_dir = os.path.join(self.workdir, 'llvm-project')
        self.repo = None  # type: Optional[git.Repo]
        self.phab_wrapper = PhabWrapper()
        self.github = self._create_github()
        self.github_repo = self.github.get_repo(MY_REPO)  # type: github.Repository

    def sync(self):
        """Sync Phabricator to Github."""
        _LOGGER.info('Starting sync...')
        self._refresh_master()
        self._delete_phab_branches()
        revisions = self.phab_wrapper.get_revisions()
        pull_requests = {p.title: p for p in self.github_repo.get_pulls(state='open')}
        for revision in revisions:
            self.create_branches_for_revision(revision)
            if self._has_branch(revision):
                if self._branches_identical(revision.branch_name, 'origin/{}'.format(revision.branch_name)):
                    _LOGGER.info('Branch {} is identical to upstream. Not pushing.'.format(revision.branch_name))
                else:
                    _LOGGER.info('Pushing branch {} to github...'.format(revision.branch_name))
                    # TODO: do we sill need to force-push?
                    self.repo.git.push('--force', 'origin', revision.branch_name)
                if revision.pr_title in pull_requests:
                    _LOGGER.info('Pull request already exists: {}'.format(pull_requests[revision.pr_title].html_url))
                else:
                    _LOGGER.info('Creating pull-request for branch {}...'.format(revision.branch_name))
                    pr = self.github_repo.create_pull(title=revision.pr_title,
                                                      body=revision.pr_summary,
                                                      head=revision.branch_name,
                                                      base='master')
                    _LOGGER.info(pr.html_url)
        _LOGGER.info('Sync completed.')

    def _refresh_master(self):
        """Clone/update local git repo."""
        if not os.path.exists(self.workdir):
            os.mkdir(self.workdir)
        if os.path.exists(self.llvm_dir):
            # TODO: in case of errors: delete and clone
            _LOGGER.info('pulling origin and upstream...')
            self.repo = git.Repo(self.llvm_dir)
            self.repo.git.fetch('--all')
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

    def create_branches_for_revision(self, revision: Revision):
        """Create branches for a Revision and it's Diffs.

        Apply changes from Phabricator to these branches.
        """
        name = revision.branch_name
        # TODO: only look at diffs that were not yet applied
        # TODO: can diffs be modified on Phabricator and keep their ID?
        for diff in revision.sorted_diffs:
            if self._has_branch(diff):
                continue
            self.create_branch_for_diff(diff)
            patch = self.phab_wrapper.get_raw_patch(diff)
            try:
                self.apply_patch(diff, patch)
            except ApplyPatchException as e:
                # TODO: retry on master if this fails
                _LOGGER.error('Could not apply patch for Diff {}. Deleting branch'.format(diff.id))
                _LOGGER.exception(e)
                self.repo.heads['master'].checkout()
                self.repo.delete_head(diff.branch_name)

        diffs = [d for d in revision.sorted_diffs if self._has_branch(d)]
        if len(diffs) == 0:
            # TODO: handle error
            _LOGGER.error('Could not create branch for Revision D{}'.format(revision.id))
            return
        new_branch = self.repo.create_head(revision.branch_name, diffs[0].branch_name)
        new_branch.checkout()

        for diff in diffs[1:]:
            _LOGGER.info('Applying Diff {} onto branch {}'.format(diff.branch_name, revision.branch_name))
            patch = self._create_patch(revision.branch_name, diff.branch_name)
            if len(patch) == 0:
                _LOGGER.warning('Diff {} is identical to last one.'.format(diff.id))
            else:
                try:
                    self.apply_patch(diff, patch)
                except ApplyPatchException:
                    _LOGGER.error('Applying patch failed, but should not:')
                    _LOGGER.error(patch)
                    raise

        _LOGGER.info('Created branch for Revision D{}'.format(revision.id))

    def create_branch_for_diff(self, diff: "Diff"):
        """Create a branch for diff."""
        base_hash = diff.base_hash
        if base_hash is None:
            base_hash = 'upstream/master'
        _LOGGER.info('creating branch {} based on {}...'.format(diff.branch_name, base_hash))
        try:
            new_branch = self.repo.create_head(diff.branch_name, base_hash)
        except ValueError:
            # commit hash not found, try again with master
            _LOGGER.warning('commit hash {} not found in upstream repository. '
                            'Trying master instead...'.format(diff.branch_name, base_hash))
            base_hash = 'upstream/master'
            new_branch = self.repo.create_head(diff.branch_name, base_hash)
        self.repo.head.reference = new_branch
        self.repo.head.reset(index=True, working_tree=True)

    def apply_patch(self, diff: "Diff", raw_patch: str):
        """Apply a patch to the working copy."""
        proc = subprocess.run('git apply --ignore-whitespace --whitespace=fix -', input=raw_patch, shell=True,
                              text=True, cwd=self.repo.working_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode != 0:
            raise ApplyPatchException('Applying patch failed:\n{}'.format(proc.stdout + proc.stderr))
        self.repo.git.add('-A')
        self.repo.index.commit(message='applying Diff {} for Revision D{}\n\n  Diff: {}'.format(
            diff.id, diff.revision.id, diff.id))

    @staticmethod
    def _create_github() -> github.Github:
        """Create instance of Github client.

        Reads access token from a file.
        """
        with open(os.path.expanduser('~/.llvm-premerge-checks/github-token.json')) as json_file:
            token = json.load(json_file)['token']
        return github.Github(token)

    def _has_branch(self, item: Union["Diff", "Revision"]) -> bool:
        """Check if the Diff/Revision has a local branch."""
        return item.branch_name in self.repo.heads

    def _delete_phab_branches(self):
        """Delete all branches sarting with 'phab-'."""
        _LOGGER.info('Deleting local Phabricator-relates branches...')
        self.repo.git.checkout('master')
        for branch in [b for b in self.repo.heads if b.name.startswith('phab-')]:
            _LOGGER.info('Deleding branch {}'.format(branch))
            self.repo.git.branch('-D', branch.name)

    def _create_patch(self, base: str, changes: str) -> str:
        """Create patch from two commits."""
        proc = subprocess.run('git diff {} {}'.format(base, changes), shell=True, text=True,
                              cwd=self.repo.working_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode != 0:
            raise ApplyPatchException('Applying patch failed:\n{}'.format(proc.stdout + proc.stderr))
        return proc.stdout

    def _branches_identical(self, left, right) -> bool:
        """Check if two branches are identical."""
        try:
            patch = self.repo.git.diff(left, right)
        except git.GitCommandError:
            return False
        if len(patch) == 0:
            return True
        return False


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    rootdir = os.path.dirname(os.path.abspath(__file__))
    tmpdir = os.path.join(rootdir, 'tmp')
    p2g = Phab2Github(tmpdir)
    p2g.sync()
