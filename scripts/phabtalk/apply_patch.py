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

import backoff
from phabricator import Phabricator


class ApplyPatch:

    def __init__(self, comment_file_path: str, git_hash: str):
        # TODO: turn os.environ parameter into command line arguments
        # this would be much clearer and easier for testing
        self.comment_file_path = comment_file_path
        self.conduit_token = os.environ.get('CONDUIT_TOKEN')  # type: Optional[str]
        self.host = os.environ.get('PHABRICATOR_HOST')  # type: Optional[str]
        self._load_arcrc()
        self.diff_id = os.environ['DIFF_ID']  # type: str
        self.diff_json_path = os.environ['DIFF_JSON']  # type: str
        if not self.host.endswith('/api/'):
            self.host += '/api/'
        self.phab = Phabricator(token=self.conduit_token, host=self.host)
        self.git_hash = git_hash  # type: Optional[str]
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

    @backoff.on_exception(backoff.expo, Exception, max_tries=5, logger='', factor=3)
    def update_interfaces(self):
        self.phab.update_interfaces()

    def run(self):
        """try to apply the patch from phabricator
        """
        self.update_interfaces()

        try:
            if self.git_hash is None:
                self._get_parent_hash()
            else:
                print('Use provided commit {}'.format(self.git_hash))
            self._git_checkout()
            self._apply_patch()
        finally:
            self._write_error_message()

    def _get_parent_hash(self):
        diff = self.phab.differential.getdiff(diff_id=self.diff_id)
        # Keep a copy of the Phabricator answer for later usage in a json file
        try:
            with open(self.diff_json_path, 'w') as json_file:
                json.dump(diff.response, json_file, sort_keys=True, indent=4)
            print('Wrote diff details to "{}".'.format(self.diff_json_path))
        except Exception:
            print('WARNING: could not write build/diff.json log file')
        self.git_hash = diff['sourceControlBaseRevision']

    @backoff.on_exception(backoff.expo, Exception, max_tries=5, logger='', factor=3)
    def _git_checkout(self):
        try:
            print('Checking out git hash {}'.format(self.git_hash))
            subprocess.check_call('git reset --hard {}'.format(self.git_hash),
                                  stdout=sys.stdout, stderr=sys.stderr, shell=True)
        except subprocess.CalledProcessError:
            print('WARNING: checkout of hash failed, using main branch instead.')
            self.msg += [
                'Could not check out parent git hash "{}". It was not found in '
                'the repository. Did you configure the "Parent Revision" in '
                'Phabricator properly? Trying to apply the patch to the '
                'main branch instead...'.format(self.git_hash)]
            subprocess.check_call('git checkout main', stdout=sys.stdout,
                                  stderr=sys.stderr, shell=True)
        subprocess.check_call('git show -s', stdout=sys.stdout,
                              stderr=sys.stderr, shell=True)
        print('git checkout completed.')

    @backoff.on_exception(backoff.expo, Exception, max_tries=5, logger='', factor=3)
    def _apply_patch(self):
        print('running arc patch...')
        cmd = 'arc patch --force --nobranch --no-ansi --diff "{}" --nocommit ' \
              '--conduit-token "{}" --conduit-uri "{}"'.format(
            self.diff_id, self.conduit_token, self.host)
        result = subprocess.run(cmd, capture_output=True, shell=True, text=True)
        print(result.stdout + result.stderr)
        if result.returncode != 0:
            msg = (
                'ERROR: arc patch failed with error code {}. '
                'Check build log for details.'.format(result.returncode))
            self.msg += [msg]
            raise Exception(msg)
        print('Patching completed.')

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
    parser.add_argument('--comment-file', type=str, dest='comment_file_path', default=None)
    parser.add_argument('--commit', type=str, dest='commit', default=None, help='use explicitly specified base commit')
    args = parser.parse_args()
    patcher = ApplyPatch(args.comment_file_path, args.commit)
    patcher.run()
