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
import logging
import os
import re
import subprocess
import sys
from typing import List, Optional, Tuple, Dict

import backoff
from buildkite_utils import annotate, feedback_url, upload_file
import git
from phabricator import Phabricator

"""URL of upstream LLVM repository."""
LLVM_GITHUB_URL = 'ssh://git@github.com/llvm/llvm-project'
FORK_REMOTE_URL = 'ssh://git@github.com/llvm-premerge-tests/llvm-project'

"""How far back the script searches in the git history to find Revisions that
have already landed. """
APPLIED_SCAN_LIMIT = datetime.timedelta(days=90)


class ApplyPatch:
    """Apply a diff from Phabricator on local working copy.

    This script is a rewrite of `arc patch` to accommodate for dependencies
    that have already landed, but could not be identified by `arc patch`.

    For a given diff_id, this class will get the dependencies listed on Phabricator.
    For each dependency D it will check the diff history:
    - if D has already landed, skip it.
    - If D has not landed, it will download the patch for D and try to apply it locally.
    Once this class has applied all dependencies, it will apply the original diff.

    This script must be called from the root folder of a local checkout of 
    https://github.com/llvm/llvm-project or given a path to clone into.
    """

    def __init__(self, path: str, diff_id: int, token: str, url: str, git_hash: str,
                 phid: str, push_branch: bool = False):
        self.push_branch = push_branch  # type: bool
        self.conduit_token = token  # type: Optional[str]
        self.host = url  # type: Optional[str]
        self.diff_id = diff_id  # type: int
        self.phid = phid  # type: str
        if not self.host.endswith('/api/'):
            self.host += '/api/'
        self.phab = self.create_phab()
        self.base_revision = git_hash  # type: str
        self.branch_base_hexsha = ''
        self.apply_diff_counter = 0
        self.build_dir = os.getcwd()
        self.revision_id = ''

        if not os.path.isdir(path):
            logging.info(f'{path} does not exist, cloning repository...')
            self.repo = git.Repo.clone_from(FORK_REMOTE_URL, path)
        else:
            logging.info('repository exist, will reuse')
            self.repo = git.Repo(path)  # type: git.Repo
            self.repo.remote('origin').set_url(FORK_REMOTE_URL)
        os.chdir(path)
        logging.info(f'working dir {os.getcwd()}')

    @property
    def branch_name(self):
        """Name used for the git branch."""
        return f'phab-diff-{self.diff_id}'

    def run(self):
        """try to apply the patch from phabricator
        """
        try:
            diff = self.get_diff(self.diff_id)
            revision = self.get_revision(diff.revisionID)
            url = f"https://reviews.llvm.org/D{revision['id']}?id={diff['id']}"
            annotate(f"Patching changes [{url}]({url})", style='info', context='patch_diff')
            self.reset_repository()
            self.revision_id = revision['id']
            dependencies = self.get_dependencies(revision)
            dependencies.reverse()  # Now revisions will be from oldest to newest.
            missing, landed = self.classify_revisions(dependencies)
            if len(dependencies) > 0:
                logging.info('This diff depends on: {}'.format(revision_list_to_str(dependencies)))
                logging.info('  Already landed: {}'.format(revision_list_to_str(landed)))
                logging.info('  Will be applied: {}'.format(revision_list_to_str(missing)))
            plan = []
            for r in missing:
                d = self.get_diff(r['diffs'][0])
                plan.append((r, d))
            plan.append((revision, diff))
            logging.info('Planning to apply in order:')
            for (r, d) in plan:
                logging.info(f"https://reviews.llvm.org/D{r['id']}?id={d['id']}")
            # Pick the newest known commit as a base for patches.
            base_commit = None
            for (r, d) in plan:
                c = self.find_commit(d['sourceControlBaseRevision'])
                if c is None:
                    logging.warning(f"D{r['id']}#{d['id']} commit {d['sourceControlBaseRevision']} does not exist")
                    continue
                if base_commit is None:
                    logging.info(f"D{r['id']}#{d['id']} commit {c.hexsha} exists")
                    base_commit = c
                elif c.committed_datetime > base_commit.committed_datetime:
                    logging.info(f"D{r['id']}#{d['id']} commit {c.hexsha} has a later commit date then"
                                 f"{base_commit.hexsha}")
                    base_commit = c
            if self.base_revision != 'auto':
                logging.info(f'Base revision "{self.base_revision}" is set by command argument. Will use '
                             f'instead of resolved "{base_commit}"')
                base_commit = self.find_commit(self.base_revision)
            if base_commit is None:
                base_commit = self.repo.heads['master'].commit
                annotate(f"Cannot find a base git revision. Will use current HEAD.",
                         style='warning', context='patch_diff')
            self.create_branch(base_commit)
            for (r, d) in plan:
                if not self.apply_diff(d, r):
                    return 1
            if self.push_branch:
                self.repo.git.push('--force', 'origin', self.branch_name)
                annotate(f"Created branch [{self.branch_name}]"
                         f"(https://github.com/llvm-premerge-tests/llvm-project/tree/{self.branch_name}).\n\n"
                         f"To checkout locally, run in your copy of llvm-project directory:\n\n"
                         "```shell\n"
                         "git remote add premerge git@github.com:llvm-premerge-tests/llvm-project.git #first time\n"
                         f"git fetch premerge {self.branch_name}\n"
                         f"git checkout -b {self.branch_name} --track premerge/{self.branch_name}\n"
                         "```",
                         style='success',
                         context='patch_diff')
                logging.info('Branch {} has been pushed'.format(self.branch_name))
            return 0
        except Exception as e:
            annotate(f":bk-status-failed: Unexpected error. Consider [creating a bug]({feedback_url()}).",
                     style='error', context='patch_diff')
            logging.error(f'exception: {e}')
            return 1

    @backoff.on_exception(backoff.expo, Exception, max_tries=5, logger='', factor=3)
    def reset_repository(self):
        """Update local git repo and origin.

        As origin is disjoint from upstream, it needs to be updated by this script.
        """
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
        if self.push_branch:
            self.repo.git.push('origin', 'master')

    @backoff.on_exception(backoff.expo, Exception, max_tries=5, logger='', factor=3)
    def find_commit(self, rev):
        try:
            return self.repo.commit(rev)
        except ValueError as e:
            return None

    @backoff.on_exception(backoff.expo, Exception, max_tries=5, logger='', factor=3)
    def create_branch(self, base_commit: git.Commit):
        if self.branch_name in self.repo.heads:
            self.repo.delete_head('--force', self.branch_name)
        logging.info(f'creating branch {self.branch_name} at {base_commit.hexsha}')
        new_branch = self.repo.create_head(self.branch_name, base_commit.hexsha)
        self.repo.head.reference = new_branch
        self.repo.head.reset(index=True, working_tree=True)
        self.branch_base_hexsha = self.repo.head.commit.hexsha
        logging.info('Base branch revision is {}'.format(self.repo.head.commit.hexsha))
        annotate(f"Branch {self.branch_name} base revision is `{self.branch_base_hexsha}`.",
                 style='info', context='patch_diff')

    @backoff.on_exception(backoff.expo, Exception, max_tries=5, logger='', factor=3)
    def commit(self, revision: Dict, diff: Dict):
        """Commit the current state and annotates with the revision info."""
        self.repo.git.add('-A')
        diff.setdefault('authorName', 'unknown')
        diff.setdefault('authorEmail', 'unknown')
        author = git.Actor(name=diff['authorName'], email=diff['authorEmail'])
        message = (f"{revision['title']}\n\n"
                   f"Automated commit created by applying diff {self.diff_id}\n"
                   f"\n"
                   f"Phabricator-ID: {self.phid}\n"
                   f"Review-ID: {diff_to_str(revision['id'])}\n")
        self.repo.index.commit(message=message, author=author)

    @backoff.on_exception(backoff.expo, Exception, max_tries=5, logger='', factor=3)
    def create_phab(self):
        phab = Phabricator(token=self.conduit_token, host=self.host)
        phab.update_interfaces()
        return phab

    @backoff.on_exception(backoff.expo, Exception, max_tries=5, logger='', factor=3)
    def get_diff(self, diff_id: int):
        """Get a diff from Phabricator based on it's diff id."""
        return self.phab.differential.getdiff(diff_id=diff_id)

    @backoff.on_exception(backoff.expo, Exception, max_tries=5, logger='', factor=3)
    def get_revision(self, revision_id: int):
        """Get a revision from Phabricator based on its revision id."""
        return self.phab.differential.query(ids=[revision_id])[0]

    @backoff.on_exception(backoff.expo, Exception, max_tries=5, logger='', factor=3)
    def get_revisions(self, *, phids: List[str] = None):
        """Get a list of revisions from Phabricator based on their PH-IDs."""
        if phids is None:
            raise Exception('_get_revisions phids is None')
        if not phids:
            # Handle an empty query locally. Otherwise the connection
            # will time out.
            return []
        return self.phab.differential.query(phids=phids)

    def get_dependencies(self, revision: Dict) -> List[Dict]:
        """Recursively resolves dependencies of the given revision.
        They are listed in reverse chronological order - from most recent to least recent."""
        dependency_ids = revision['auxiliary']['phabricator:depends-on']
        revisions = self.get_revisions(phids=dependency_ids)
        result = []
        for r in revisions:
            result.append(r)
            sub = self.get_dependencies(r)
            result.extend(sub)
        return result

    def apply_diff(self, diff: Dict, revision: Dict) -> bool:
        """Download and apply a diff to the local working copy."""
        logging.info(f"Applying {diff['id']} for revision {revision['id']}...")
        patch = self.get_raw_diff(str(diff['id']))
        self.apply_diff_counter += 1
        patch_file = f"{self.apply_diff_counter}_{diff['id']}.patch"
        with open(os.path.join(self.build_dir, patch_file), 'wt') as f:
            f.write(patch)
        # For annotate to properly link this file it must exist before the upload.
        upload_file(self.build_dir, patch_file)
        logging.debug(f'raw patch:\n{patch}')
        proc = subprocess.run('git apply -', input=patch, shell=True, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode != 0:
            logging.info(proc.stdout)
            logging.error(proc.stderr)
            message = f":bk-status-failed: Failed to apply [{patch_file}](artifact://{patch_file}).\n\n"
            if self.revision_id != revision['id']:
                message += f"**Attention! D{revision['id']} is one of the dependencies of the target " \
                           f"revision D{self.revision_id}.**\n\n"
            message += (f"No testing is possible because we couldn't apply the patch.\n\n"
                        f"---\n\n"
                        '### Troubleshooting\n\n'
                        'More information is available in the log of of *create branch* step. '
                        f"All patches applied are available as *Artifacts*.\n\n"
                        f":bulb: The patch may not apply if it includes only the most recent of "
                        f"multiple local commits. Try to upload a patch with\n"
                        f"```shell\n"
                        f"arc diff `git merge-base HEAD origin` --update D{revision['id']}\n"
                        f"```\n\n"
                        f"to include all local changes.\n\n"
                        '---\n\n'
                        f"If this case could have been handled better, please [create a bug]({feedback_url()}).")
            annotate(message,
                     style='error',
                     context='patch_diff')
            return False
        self.commit(revision, diff)
        return True

    @backoff.on_exception(backoff.expo, Exception, max_tries=5, logger='', factor=3)
    def get_raw_diff(self, diff_id: str) -> str:
        return self.phab.differential.getrawdiff(diffID=diff_id).response

    def get_landed_revisions(self):
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

    def classify_revisions(self, revisions: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """Check which of the dependencies have already landed on the current branch."""
        landed_deps = []
        missing_deps = []
        for d in revisions:
            if diff_to_str(d['id']) in self.get_landed_revisions():
                landed_deps.append(d)
            else:
                missing_deps.append(d)
        return missing_deps, landed_deps


def diff_to_str(diff: int) -> str:
    """Convert a diff id to a string with leading "D"."""
    return 'D{}'.format(diff)


def revision_list_to_str(diffs: List[Dict]) -> str:
    """Convert list of diff ids to a comma separated list, prefixed with "D"."""
    return ', '.join([diff_to_str(d['id']) for d in diffs])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Apply Phabricator patch to working directory.')
    parser.add_argument('diff_id', type=int)
    parser.add_argument('--path', type=str, help='repository path', default=os.getcwd())
    parser.add_argument('--token', type=str, default=None, help='Conduit API token')
    parser.add_argument('--url', type=str, default='https://reviews.llvm.org', help='Phabricator URL')
    parser.add_argument('--commit', dest='commit', type=str, default='auto',
                        help='Use this commit as a base. For "auto" tool tries to pick the base commit itself')
    parser.add_argument('--push-branch', action='store_true', dest='push_branch',
                        help='choose if branch shall be pushed to origin')
    parser.add_argument('--phid', type=str, default=None, help='Phabricator ID of the review this commit pertains to')
    parser.add_argument('--log-level', type=str, default='INFO')
    args = parser.parse_args()
    logging.basicConfig(level=args.log_level, format='%(levelname)-7s %(message)s')
    patcher = ApplyPatch(args.path, args.diff_id, args.token, args.url, args.commit, args.phid, args.push_branch)
    sys.exit(patcher.run())
