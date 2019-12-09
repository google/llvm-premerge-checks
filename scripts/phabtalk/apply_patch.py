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
import subprocess
import sys
from typing import List, Optional
from phabricator import Phabricator

class ApplyPatch:

    def __init__(self, diff_id:str, comment_file_path: str, token: str, url: str, store_json_diff: str):
        # TODO: turn os.environ parameter into command line arguments
        # this would be much clearer and easier for testing
        self.comment_file_path = comment_file_path
        self.conduit_token = token   # type: Optional[str]
        self.host = url  # type: Optional[str]
        self._load_arcrc()
        self.diff_id = diff_id  # type: str
        self.diff_json_path = store_json_diff   # type: str
        if not self.host.endswith('/api/'):
            self.host += '/api/'
        self.phab = Phabricator(token=self.conduit_token, host=self.host)
        self.git_hash = None  # type: Optional[str]
        self.msg = []  # type: List[str]

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
        self.phab.update_interfaces()

        try:
            dependencies = self._get_dependencies()
            dep_str = ', '.join(['D{}'.format(d) for d in dependencies])
            print('This diff depends on: {}'.format(dep_str))
            # self._get_parent_hash()
            # self._git_checkout()
            # self._apply_patch()
        finally:
            self._write_error_message()

    def _get_parent_hash(self) -> str:
        diff = self._get_diff(self.diff_id)
        # Keep a copy of the Phabricator answer for later usage in a json file
        try:
            with open(self.diff_json_path,'w') as json_file:
                json.dump(diff.response, json_file, sort_keys=True, indent=4)
            print('Wrote diff details to "{}".'.format(self.diff_json_path))
        except Exception:
            print('WARNING: could not write build/diff.json log file')
        self.git_hash = diff['sourceControlBaseRevision']

    def _get_diff(self, diff_id: str):
        return self.phab.differential.getdiff(diff_id=diff_id)

    def _get_revision(self, revision_id: int):
        return self.phab.differential.query(ids=[revision_id])[0]

    def _get_revisions(self, phids):
        return self.phab.differential.query(phids=phids)

    def _get_dependencies(self) -> List[int]:
        revision_id = int(self._get_diff(self.diff_id).revisionID)
        revision = self._get_revision(revision_id)
        dependency_ids = revision['auxiliary']['phabricator:depends-on']
        revisions = self._get_revisions(dependency_ids)
        diff_ids = [int(rev['id']) for rev in revisions]
        return diff_ids

    def _git_checkout(self):
        try:
            print('Checking out git hash {}'.format(self.git_hash))
            subprocess.check_call('git reset --hard {}'.format(self.git_hash), 
                stdout=sys.stdout, stderr=sys.stderr, shell=True)
        except subprocess.CalledProcessError:
            print('WARNING: checkout of hash failed, using master branch instead.')
            self.msg += [
                'Could not check out parent git hash "{}". It was not found in '
                'the repository. Did you configure the "Parent Revision" in '
                'Phabricator properly? Trying to apply the patch to the '
                'master branch instead...'.format(self.git_hash)]
            subprocess.check_call('git checkout master', stdout=sys.stdout, 
                stderr=sys.stderr, shell=True)
        print('git checkout completed.')

    def _apply_patch(self):
        # TODO
        pass

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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Apply Phabricator patch to working directory.')
    parser.add_argument('diff_id', type=str)
    parser.add_argument('--comment-file', type=str, dest='comment_file_path', default=None)
    parser.add_argument('--token', type=str, default=None)
    parser.add_argument('--url', type=str, default=None)
    parser.add_argument('--store-json-diff', dest='store_json_diff', type=str, default=None)
    args = parser.parse_args()
    patcher = ApplyPatch(args.diff_id, args.comment_file_path, args.token, args.url, args.store_json_diff)
    patcher.run()

