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

import logging
import os
import json
from phabricator import Phabricator
from typing import List, Optional, Dict
import datetime


_BASE_URL = 'https://reviews.llvm.org'

_LOGGER = logging.getLogger()


class Revision:
    """A Revision on Phabricator"""

    def __init__(self, revision_dict: Dict):
        self.revision_dict = revision_dict
        self.diffs = []  # type : "Diff"
        self.phab_url = '{}/D{}'.format(_BASE_URL, self.id)  # type: str

    @property
    def id(self) -> str:
        return self.revision_dict['id']

    @property
    def phid(self) -> str:
        return self.revision_dict['phid']

    @property
    def status(self) -> str:
        return self.revision_dict['fields']['status']['value']

    def __str__(self):
        return 'Revision {}: {} - ({})'.format(self.id, self.status,
                                               ','.join([str(d.id) for d in self.diffs]))

    @property
    def branch_name(self) -> str:
        return 'phab-D{}'.format(self.id)

    @property
    def title(self) -> str:
        return self.revision_dict['fields']['title']

    @property
    def pr_title(self) -> str:
        return 'D{}: {}'.format(self.id, self.title)

    @property
    def summary(self) -> str:
        return self.revision_dict['fields']['summary']

    @property
    def pr_summary(self) -> str:
        return '{}\n\n{}'.format(self.summary, self.phab_url)

    @property
    def sorted_diffs(self) -> List["Diff"]:
        return sorted(self.diffs, key=lambda d: d.id)


class Diff:
    """A Phabricator diff."""

    def __init__(self, diff_dict: Dict, revision: Revision):
        self.diff_dict = diff_dict
        self.revision = revision
        # TODO: check in git repo instead of using a flag

    @property
    def id(self) -> str:
        return self.diff_dict['id']

    @property
    def phid(self) -> str:
        return self.diff_dict['phid']

    def __str__(self):
        return 'Diff {}'.format(self.id)

    @property
    def base_hash(self) -> Optional[str]:
        for ref in self.diff_dict['fields']['refs']:
            if ref['type'] == 'base':
                return ref['identifier']
        return None

    @property
    def branch_name(self) -> str:
        return 'phab-diff-{}'.format(self.id)


class PhabWrapper:
    """
    Wrapper around the interactions with Phabricator.

    Conduit API documentation: https://reviews.llvm.org/conduit/
    """

    def __init__(self):
        self.conduit_token = None  # type: Optional[str]
        self.host = None  # type: Optional[str]
        self._load_arcrc()
        self.phab = self._create_phab()  # type: Phabricator

    def _load_arcrc(self):
        """Load arc configuration from file if not set."""
        _LOGGER.info('Loading configuration from ~/.arcrc file')
        with open(os.path.expanduser('~/.arcrc'), 'r') as arcrc_file:
            arcrc = json.load(arcrc_file)
        # use the first host configured in the file
        self.host = next(iter(arcrc['hosts']))
        self.conduit_token = arcrc['hosts'][self.host]['token']

    def _create_phab(self) -> Phabricator:
        """Create Phabricator API instance and update it."""
        phab = Phabricator(token=self.conduit_token, host=self.host)
        # TODO: retry on communication error
        phab.update_interfaces()
        return phab

    def get_revisions(self) -> List[Revision]:
        """Get relevant revisions."""
        # TODO: figure out which revisions we really need to pull in
        _LOGGER.info('Getting revisions from Phabricator')
        start_date = datetime.datetime.now() - datetime.timedelta(days=3)
        constraints = {
            'createdStart': int(start_date.timestamp())
            #'ids': [76120]
        }
        # TODO: handle > 100 responses
        revision_response = self.phab.differential.revision.search(
                constraints=constraints)
        revisions = [Revision(r) for r in revision_response.response['data']]
        # TODO: only taking the first 10 to speed things up
        revisions = revisions[0:10]
        _LOGGER.info('Got {} revisions from the server'.format(len(revisions)))
        for revision in revisions:
            # TODO: batch-query diffs for all revisions, reduce number of
            #   API calls this would be much faster. But then we need to locally
            #   map the diffs to the right revisions
            self._get_diffs(revision)
        return revisions

    def _get_diffs(self, revision: Revision):
        """Get diffs for a revision from Phabricator."""
        _LOGGER.info('Downloading diffs for Revision D{}...'.format(revision.id))
        constraints = {
            'revisionPHIDs': [revision.phid]
        }
        diff_response = self.phab.differential.diff.search(
            constraints=constraints)
        revision.diffs = [Diff(d, revision) for d in diff_response.response['data']]
        _LOGGER.info(', '.join([str(d.id) for d in revision.diffs]))

    def get_raw_patch(self, diff: Diff) -> str:
        """Get raw patch for diff from Phabricator."""
        _LOGGER.info('Downloading patch for Diff {}...'.format(diff.id))
        return self.phab.differential.getrawdiff(diffID=str(diff.id)).response
