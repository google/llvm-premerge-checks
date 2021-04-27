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
"""
Interactions with Phabricator.
"""

import logging
from typing import Optional, List, Dict
import uuid
import argparse

import backoff
from phabricator import Phabricator


class PhabTalk:
    """Talk to Phabricator to upload build results.
       See https://secure.phabricator.com/conduit/method/harbormaster.sendmessage/
    """

    def __init__(self, token: Optional[str], host: Optional[str] = 'https://reviews.llvm.org/api/',
                 dry_run_updates: bool = False):
        self._phab = None  # type: Optional[Phabricator]
        self.dry_run_updates = dry_run_updates
        self._phab = Phabricator(token=token, host=host)
        self.update_interfaces()

    @backoff.on_exception(backoff.expo, Exception, max_tries=5, logger='', factor=3)
    def update_interfaces(self):
        self._phab.update_interfaces()

    @backoff.on_exception(backoff.expo, Exception, max_tries=5, logger='', factor=3)
    def get_revision_id(self, diff: str) -> Optional[str]:
        """Get the revision ID for a diff from Phabricator."""
        result = self._phab.differential.querydiffs(ids=[diff])
        return 'D' + result[diff]['revisionID']

    def comment_on_diff(self, diff_id: str, text: str):
        """Add a comment to a differential based on the diff_id"""
        logging.info('Sending comment to diff {}:'.format(diff_id))
        logging.info(text)
        revision_id = self.get_revision_id(diff_id)
        if revision_id is not None:
            self._comment_on_revision(revision_id, text)

    @backoff.on_exception(backoff.expo, Exception, max_tries=5, logger='', factor=3)
    def _comment_on_revision(self, revision: str, text: str):
        """Add comment on a differential based on the revision id."""

        transactions = [{
            'type': 'comment',
            'value': text
        }]

        if self.dry_run_updates:
            logging.info('differential.revision.edit =================')
            logging.info('Transactions: {}'.format(transactions))
            return

        # API details at
        # https://secure.phabricator.com/conduit/method/differential.revision.edit/
        self._phab.differential.revision.edit(objectIdentifier=revision,
                                              transactions=transactions)
        logging.info('Uploaded comment to Revision D{}:{}'.format(revision, text))

    @backoff.on_exception(backoff.expo, Exception, max_tries=5, logger='', factor=3)
    def update_build_status(self, phid: str, working: bool, success: bool, lint: {}, unit: []):
        """Submit collected report to Phabricator.
        """

        result_type = 'pass'
        if working:
            result_type = 'working'
        elif not success:
            result_type = 'fail'

        # Group lint messages by file and line.
        lint_messages = []
        for v in lint.values():
            path = ''
            line = 0
            descriptions = []
            for e in v:
                path = e['path']
                line = e['line']
                descriptions.append('{}: {}'.format(e['name'], e['description']))
            lint_message = {
                'name': 'Pre-merge checks',
                'severity': 'warning',
                'code': 'llvm-premerge-checks',
                'path': path,
                'line': line,
                'description': '\n'.join(descriptions),
            }
            lint_messages.append(lint_message)

        if self.dry_run_updates:
            logging.info('harbormaster.sendmessage =================')
            logging.info('type: {}'.format(result_type))
            logging.info('unit: {}'.format(unit))
            logging.info('lint: {}'.format(lint_messages))
            return

        self._phab.harbormaster.sendmessage(
            buildTargetPHID=phid,
            type=result_type,
            unit=unit,
            lint=lint_messages)
        logging.info('Uploaded build status {}, {} test results and {} lint results'.format(
            result_type, len(unit), len(lint_messages)))

    @backoff.on_exception(backoff.expo, Exception, max_tries=5, logger='', factor=3)
    def create_artifact(self, phid, artifact_key, artifact_type, artifact_data):
        if self.dry_run_updates:
            logging.info('harbormaster.createartifact =================')
            logging.info('artifactKey: {}'.format(artifact_key))
            logging.info('artifactType: {}'.format(artifact_type))
            logging.info('artifactData: {}'.format(artifact_data))
            return
        self._phab.harbormaster.createartifact(
            buildTargetPHID=phid,
            artifactKey=artifact_key,
            artifactType=artifact_type,
            artifactData=artifact_data)

    def maybe_add_url_artifact(self, phid: str, url: str, name: str):
        if self.dry_run_updates:
            logging.info(f'add ULR artifact "{name}" {url}')
            return
        if phid is None:
            logging.warning('PHID is not provided, cannot create URL artifact')
            return
        self.create_artifact(phid, str(uuid.uuid4()), 'uri', {'uri': url, 'ui.external': True, 'name': name})


class Step:
    def __init__(self, name=''):
        self.name = name
        self.success = True
        self.duration = 0.0
        self.reproduce_commands = []

    def set_status_from_exit_code(self, exit_code: int):
        if exit_code != 0:
            self.success = False


class Report:
    def __init__(self):
        self.os = ''
        self.name = ''
        self.comments = []
        self.success = True
        self.working = False
        self.unit = []  # type: List
        self.lint = {}
        self.test_stats = {
            'pass': 0,
            'fail': 0,
            'skip': 0
        }  # type: Dict[str, int]
        self.steps = []  # type: List[Step]
        self.artifacts = []  # type: List

    def __str__(self):
        return str(self.__dict__)

    def add_lint(self, m):
        key = '{}:{}'.format(m['path'], m['line'])
        if key not in self.lint:
            self.lint[key] = []
        self.lint[key].append(m)

    def add_artifact(self, dir: str, file: str, name: str):
        self.artifacts.append({'dir': dir, 'file': file, 'name': name})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Sample interaction with Phabricator')
    parser.add_argument('--url', type=str, dest='url', default='https://reviews.llvm.org/api/')
    parser.add_argument('--token', type=str, dest='token', default=None, required=True)
    parser.add_argument('--diff_id', type=str, dest='diff_id', default=None, required=True)
    args = parser.parse_args()
    phabtalk = PhabTalk(args.token, args.url, False)
    print(phabtalk.get_revision_id(args.diff_id))

