#!/usr/bin/env python3
# Copyright 2019 Google LLC
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
import json
import os
import re
import subprocess
from typing import List, Optional, Tuple

from phabricator import Phabricator
from git import Repo, GitCommandError


class ApplyPatch:
    """Apply a diff from Phabricator on local working copy.

    This script is a rewrite of `arc patch` to accomodate for dependencies
    that have already landed, but could not be identified by `arc patch`.

    For a given diff_id, this class will get the dependencies listed on Phabricator.
    For each dependency D it will check the diff history:
    - if D has already landed, skip it.
    - If D has not landed, it will download the patch for D and try to apply it locally.
    Once this class has applied all dependencies, it will apply the diff itself.

    This script must be called from the root folder of a local checkout of 
    https://github.com/llvm/llvm-project
    """

    def __init__(self, diff_id: int, comment_file_path: str, token: str, url: str, git_hash: str):
        self.comment_file_path = comment_file_path
        self.conduit_token = token  # type: Optional[str]
        self.host = url  # type: Optional[str]
        self._load_arcrc()
        self.diff_id = diff_id  # type: int
        if not self.host.endswith('/api/'):
            self.host += '/api/'
        self.phab = self._create_phab()
        self.base_revision = git_hash  # type: Optional[str]
        self.msg = []  # type: List[str]
        self.repo = Repo(os.getcwd())  # type: Repo

    def _load_arcrc(self):
        """Load arc configuration from file if not set."""
        if self.conduit_token is not None or self.host is not None:
            return
        print('Loading configuration from ~/.arcrc file')
        with open(os.path.expanduser('~/.arcrc'), 'r') as arcrc_file:
            arcrc = json.load(arcrc_file)
        # use the first host configured in the file
        self.host = next(iter(arcrc['hosts']))
        self.conduit_token = arcrc['hosts'][self.host]['token']

    def run(self):
        """try to apply the patch from phabricator
        
        Write to `self.comment_file` for showing error messages on Phabricator.
        """

        try:
            revision_id, dependencies, base_revision = self._get_dependencies(self.diff_id)
            dependencies.reverse()  # Arrange deps in chronological order.
            if self.base_revision is not None:
                print('Using base revision provided by command line\n{} instead of resolved\n{}'.format(
                    self.base_revision, base_revision))
                base_revision = self.base_revision
            print('Checking out {}...'.format(base_revision))
            try:
                self.repo.git.checkout(base_revision)
            except GitCommandError:
                print('ERROR checking out revision {}. It`s not in the '
                      'repository. Using master instead.'.format(base_revision))
                self.repo.git.checkout('master')
            print('Revision is {}'.format(self.repo.head.commit.hexsha))
            print('git reset, git cleanup...')
            self.repo.git.reset('--hard')
            self.repo.git.clean('-fdx')
            print('Analyzing {}'.format(diff_to_str(revision_id)))
            if len(dependencies) > 0:
                print('This diff depends on: {}'.format(diff_list_to_str(dependencies)))
                missing, landed = self._get_missing_landed_dependencies(dependencies)
                print('  Already landed: {}'.format(diff_list_to_str(landed)))
                print('  Will be applied: {}'.format(diff_list_to_str(missing)))
                if missing:
                    for revision in missing:
                        self._apply_revision(revision)
                    self.repo.config_writer().set_value("user", "name", "myusername").release()
                    self.repo.config_writer().set_value("user", "email", "myemail@example.com").release()
                    self.repo.git.commit('-a', '-m', 'dependencies')
                print('All depended diffs are applied')
            self._apply_diff(self.diff_id, revision_id)
            print('done.')
        finally:
            self._write_error_message()

    def _create_phab(self):
        phab = Phabricator(token=self.conduit_token, host=self.host)
        phab.update_interfaces()
        return phab

    def _get_diff(self, diff_id: int):
        """Get a diff from Phabricator based on it's diff id."""
        return self.phab.differential.getdiff(diff_id=diff_id)

    def _get_revision(self, revision_id: int):
        """Get a revision from Phabricator based on its revision id."""
        return self.phab.differential.query(ids=[revision_id])[0]

    def _get_revisions(self, *, phids: List[str] = None):
        """Get a list of revisions from Phabricator based on their PH-IDs."""
        if phids is None:
            raise Exception('_get_revisions phids is None')
        if not phids:
            # Handle an empty query locally. Otherwise the connection
            # will time out.
            return []
        return self.phab.differential.query(phids=phids)

    def _get_dependencies(self, diff_id) -> Tuple[int, List[int], str]:
        """Get all dependencies for the diff.
        They are listed in reverse chronological order - from most recent to least recent."""

        print('Getting dependencies of {}'.format(diff_id))
        diff = self._get_diff(diff_id)
        revision_id = int(diff.revisionID)
        revision = self._get_revision(revision_id)
        base_revision = diff['sourceControlBaseRevision']
        if base_revision is None or len(base_revision) == 0:
            base_revision = 'master'
        dependency_ids = revision['auxiliary']['phabricator:depends-on']
        revisions = self._get_revisions(phids=dependency_ids)
        result = []
        # Recursively resolve dependencies of those diffs.
        for r in revisions:
            _, sub, _ = self._get_dependencies(r['diffs'][0])
            result.append(r['id'])
            result.extend(sub)

        return revision_id, result, base_revision

    def _apply_diff(self, diff_id: int, revision_id: int):
        """Download and apply a diff to the local working copy."""
        print('Applying diff {} for revision {}...'.format(diff_id, diff_to_str(revision_id)))
        # TODO: print diff or URL to it
        diff = self.phab.differential.getrawdiff(diffID=str(diff_id)).response
        proc = subprocess.run('patch -p1', input=diff, shell=True, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode != 0:
            raise Exception('Applying patch failed:\n{}'.format(proc.stdout + proc.stderr))

    def _apply_revision(self, revision_id: int):
        """Download and apply the latest  diff of a revision to the local working copy."""
        revision = self._get_revision(revision_id)
        # take the diff_id with the highest number, this should be latest one
        diff_id = max(revision['diffs'])
        self._apply_diff(diff_id, revision_id)

    def _write_error_message(self):
        """Write the log message to a file."""
        if self.comment_file_path is None:
            return

        if len(self.msg) == 0:
            return
        print('writing error message to {}'.format(self.comment_file_path))
        with open(self.comment_file_path, 'a') as comment_file:
            text = '\n\n'.join(self.msg)
            comment_file.write(text)

    def _get_landed_revisions(self, limit: int = 1000):
        """Get list of landed revisions from current git branch."""
        diff_regex = re.compile(r'^Differential Revision: https:\/\/reviews\.llvm\.org\/(.*)$', re.MULTILINE)
        earliest_commit = None
        rev = self.base_revision
        if rev is None:
            rev = 'master'
        for commit in self.repo.iter_commits(rev, max_count=limit):
            earliest_commit = commit
            result = diff_regex.search(commit.message)
            if result is not None:
                yield result.group(1)
        if earliest_commit is not None:
            print('Earliest analyzed commit in history', earliest_commit.hexsha, earliest_commit.committed_datetime)
        return

    def _get_missing_landed_dependencies(self, dependencies: List[int]) -> Tuple[List[int], List[int]]:
        """Check which of the dependencies have already landed on the current branch."""
        landed_deps = []
        missing_deps = []
        for dependency in dependencies:
            if diff_to_str(dependency) in self._get_landed_revisions():
                landed_deps.append(dependency)
            else:
                missing_deps.append(dependency)
        return missing_deps, landed_deps


def diff_to_str(diff: int) -> str:
    """Convert a diff id to a string with leading "D"."""
    return 'D{}'.format(diff)


def diff_list_to_str(diffs: List[int]) -> str:
    """Convert list of diff ids to a comma separated list, prefixed with "D"."""
    return ', '.join([diff_to_str(d) for d in diffs])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Apply Phabricator patch to working directory.')
    parser.add_argument('diff_id', type=int)
    # TODO: instead of --comment-file use stdout / stderr.
    parser.add_argument('--comment-file', type=str, dest='comment_file_path', default=None)
    parser.add_argument('--token', type=str, default=None, help='Conduit API token')
    parser.add_argument('--url', type=str, default=None, help='Phabricator URL')
    parser.add_argument('--commit', dest='commit', type=str, default=None,
                        help='Use this commit as a base. By default tool tries to pick the base commit itself')
    args = parser.parse_args()
    patcher = ApplyPatch(args.diff_id, args.comment_file_path, args.token, args.url, args.commit)
    patcher.run()
