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
import datetime
import json
import logging
import os
import re
import socket
import subprocess
import sys
import time
from typing import List, Optional, Tuple

from phabricator import Phabricator
from git import Repo, BadName, GitCommandError


# FIXME: maybe move to config file
"""URL of upstream LLVM repository."""
LLVM_GITHUB_URL = 'ssh://git@github.com/llvm/llvm-project'
FORK_REMOTE_URL = 'ssh://git@github.com/llvm-premerge-tests/llvm-project'

"""How far back the script searches in the git history to find Revisions that
have already landed. """
APPLIED_SCAN_LIMIT = datetime.timedelta(days=90)


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
    https://github.com/llvm/llvm-project or given a path to clone into.
    """

    def __init__(self, path: str, diff_id: int, token: str, url: str, git_hash: str,
                 phid: str, push_branch: bool = False):
        self.push_branch = push_branch  # type: bool
        self.conduit_token = token  # type: Optional[str]
        self.host = url  # type: Optional[str]
        self._load_arcrc()
        self.diff_id = diff_id  # type: int
        self.phid = phid # type: str
        if not self.host.endswith('/api/'):
            self.host += '/api/'
        self.phab = self._create_phab()
        self.base_revision = git_hash  # type: str

        if not os.path.isdir(path):
            logging.info(f'{path} does not exist, cloning repository')
            # TODO: progress of clonning
            self.repo = Repo.clone_from(FORK_REMOTE_URL, path)
        else:
            logging.info('repository exist, will reuse')
            self.repo = Repo(path)  # type: Repo
            # TODO: set origin url to fork
        os.chdir(path)
        logging.info(f'working dir {os.getcwd()}')

    @property
    def branch_name(self):
        """Name used for the git branch."""
        return 'phab-diff-{}'.format(self.diff_id)

    def _load_arcrc(self):
        """Load arc configuration from file if not set."""
        if self.conduit_token is not None or self.host is not None:
            return
        logging.info('Loading configuration from ~/.arcrc file')
        with open(os.path.expanduser('~/.arcrc'), 'r') as arcrc_file:
            arcrc = json.load(arcrc_file)
        # use the first host configured in the file
        self.host = next(iter(arcrc['hosts']))
        self.conduit_token = arcrc['hosts'][self.host]['token']

    def run(self):
        """try to apply the patch from phabricator

        """

        try:
            self._refresh_master()
            revision_id, dependencies, base_revision = self._get_dependencies(self.diff_id)
            dependencies.reverse()  # Arrange deps in chronological order.
            if self.base_revision != 'auto':
                logging.info('Using base revision provided by command line\n{} instead of resolved\n{}'.format(
                    self.base_revision, base_revision))
                base_revision = self.base_revision
            self._create_branch(base_revision)
            logging.info('git reset, git cleanup...')
            self.repo.git.reset('--hard')
            self.repo.git.clean('-ffxdq')
            logging.info('Analyzing {}'.format(diff_to_str(revision_id)))
            if len(dependencies) > 0:
                logging.info('This diff depends on: {}'.format(diff_list_to_str(dependencies)))
                missing, landed = self._get_missing_landed_dependencies(dependencies)
                logging.info('  Already landed: {}'.format(diff_list_to_str(landed)))
                logging.info('  Will be applied: {}'.format(diff_list_to_str(missing)))
                if missing:
                    for revision in missing:
                        self._apply_revision(revision)
                    # FIXME: submit every Revision individually to get nicer history, use original user name
                    self.repo.config_writer().set_value("user", "name", "myusername").release()
                    self.repo.config_writer().set_value("user", "email", "myemail@example.com").release()
                    self.repo.git.commit('-a', '-m', 'dependencies')
                logging.info('All depended diffs are applied')
            logging.info('applying original diff')
            self._apply_diff(self.diff_id, revision_id)
            if self.push_branch:
                self._commit_and_push()
            else:
                self.repo.git.add('-u', '.')
            return 0
        except Exception as e:
            logging.error(f'exception: {e}')
            return 1

    def _refresh_master(self):
        """Update local git repo and origin.

        As origin is disjoint from upstream, it needs to be updated by this script.
        """
        if not self.push_branch:
            return

        logging.info('Syncing local, origin and upstream...')
        self.repo.git.clean('-ffxdq')
        self.repo.git.reset('--hard')
        self.repo.git.fetch('--all')
        self.repo.git.checkout('master')
        if 'upstream' not in self.repo.remotes:
            self.repo.create_remote('upstream', url=LLVM_GITHUB_URL)
            self.repo.remotes.upstream.fetch()
        self.repo.git.pull('origin', 'master')
        self.repo.git.pull('upstream', 'master')
        try:
            self.repo.git.push('origin', 'master')
            logging.info('refresh of master branch completed')
        except GitCommandError as e:
            logging.info('Info: Could not push to origin master.')

    def _create_branch(self, base_revision: Optional[str]):
        self.repo.git.fetch('--all')
        if self.branch_name in self.repo.heads:
            self.repo.delete_head('--force', self.branch_name)
        try:
            commit = self.repo.commit(base_revision)
        except Exception as e:
            logging.info('Cannot resolve revision {}: {}, going to use "master" instead.'.format(base_revision, e))
            commit = self.repo.heads['master'].commit
        logging.info(f'creating branch {self.branch_name} at {commit.hexsha}')
        new_branch = self.repo.create_head(self.branch_name, commit.hexsha)
        self.repo.head.reference = new_branch
        self.repo.head.reset(index=True, working_tree=True)
        logging.info('Base branch revision is {}'.format(self.repo.head.commit.hexsha))

    def _commit_and_push(self):
        """Commit the patch and push it to origin."""
        if not self.push_branch:
            return

        self.repo.git.add('-A')
        message = """
Applying diff {}

Phabricator-ID: {}
""".format(self.diff_id, self.phid)
        self.repo.index.commit(message=message)
        self.repo.git.push('--force', 'origin', self.branch_name)
        logging.info('Branch {} pushed to origin'.format(self.branch_name))
        pass

    def _create_phab(self):
        phab = Phabricator(token=self.conduit_token, host=self.host)
        try_call(lambda: phab.update_interfaces())
        return phab

    def _get_diff(self, diff_id: int):
        """Get a diff from Phabricator based on it's diff id."""
        return try_call(lambda: self.phab.differential.getdiff(diff_id=diff_id))

    def _get_revision(self, revision_id: int):
        """Get a revision from Phabricator based on its revision id."""
        return try_call(lambda: self.phab.differential.query(ids=[revision_id])[0])

    def _get_revisions(self, *, phids: List[str] = None):
        """Get a list of revisions from Phabricator based on their PH-IDs."""
        if phids is None:
            raise Exception('_get_revisions phids is None')
        if not phids:
            # Handle an empty query locally. Otherwise the connection
            # will time out.
            return []
        return try_call(lambda: self.phab.differential.query(phids=phids))

    def _get_dependencies(self, diff_id) -> Tuple[int, List[int], str]:
        """Get all dependencies for the diff.
        They are listed in reverse chronological order - from most recent to least recent."""

        logging.info('Getting dependencies of {}'.format(diff_id))
        diff = self._get_diff(diff_id)
        logging.debug(f'diff object: {diff}')
        revision_id = int(diff.revisionID)
        revision = self._get_revision(revision_id)
        logging.debug(f'revision object: {revision}')
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
        logging.info('Applying diff {} for revision {}...'.format(diff_id, diff_to_str(revision_id)))
        diff = try_call(lambda: self.phab.differential.getrawdiff(diffID=str(diff_id)).response)
        logging.debug(f'diff {diff_id}:\n{diff}')
        proc = subprocess.run('git apply -', input=diff, shell=True, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode != 0:
            raise Exception('Applying patch failed:\n{}'.format(proc.stdout + proc.stderr))

    def _apply_revision(self, revision_id: int):
        """Download and apply the latest  diff of a revision to the local working copy."""
        revision = self._get_revision(revision_id)
        # take the diff_id with the highest number, this should be latest one
        diff_id = max(revision['diffs'])
        logging.info(f'picking diff from revision {revision_id}: {diff_id} from {revision["diffs"]}')
        self._apply_diff(diff_id, revision_id)

    def _get_landed_revisions(self):
        """Get list of landed revisions from current git branch."""
        diff_regex = re.compile(r'^Differential Revision: https://reviews\.llvm\.org/(.*)$', re.MULTILINE)
        earliest_commit = None
        rev = self.base_revision
        age_limit = datetime.datetime.now() - APPLIED_SCAN_LIMIT
        if rev == 'auto':  # FIXME: use revison that created the branch
            rev = 'master'
        for commit in self.repo.iter_commits(rev):
            if datetime.datetime.fromtimestamp(commit.committed_date) < age_limit:
                break
            earliest_commit = commit
            result = diff_regex.search(commit.message)
            if result is not None:
                yield result.group(1)
        if earliest_commit is not None:
            logging.info(f'Earliest analyzed commit in history {earliest_commit.hexsha}, '
                         f'{earliest_commit.committed_datetime}')
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


def try_call(call):
    """Tries to call function several times retrying on socked.timeout."""
    c = 0
    while True:
        try:
            return call()
        except socket.timeout as e:
            c += 1
            if c > 5:
                logging.error('Connection to Pharicator failed, giving up: {}'.format(e))
                raise
            logging.error('Connection to Pharicator failed, retrying: {}'.format(e))
            time.sleep(c * 10)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Apply Phabricator patch to working directory.')
    parser.add_argument('diff_id', type=int)
    parser.add_argument('--path', type=str, help='repository path', default=os.getcwd())
    parser.add_argument('--token', type=str, default=None, help='Conduit API token')
    parser.add_argument('--url', type=str, default=None, help='Phabricator URL')
    parser.add_argument('--commit', dest='commit', type=str, default='auto',
                        help='Use this commit as a base. For "auto" tool tries to pick the base commit itself')
    parser.add_argument('--push-branch', action='store_true', dest='push_branch',
                        help='choose if branch shall be pushed to origin')
    parser.add_argument('--phid', type=str, default=None, help='Phabricator ID of the review this commit pertains to')
    parser.add_argument('--log-level', type=str, default='INFO')
    args = parser.parse_args()
    logging.basicConfig(level=args.log_level, format='%(levelname)-7s %(message)s')
    patcher = ApplyPatch(args.path, args.diff_id, args.token, args.url, args.commit, args.push_branch)
    sys.exit(patcher.run())
