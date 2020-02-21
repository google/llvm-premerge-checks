#!/usr/bin/env pathon3
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

# Get data on Revisions and builds from Phabricator

import phabricator
import json
import os
import datetime


class PhabBuildPuller:

    def __init__(self):
        self.conduit_token = None
        self.host = None
        self.phab = self._create_phab()

    def _create_phab(self) -> phabricator.Phabricator:
        phab = phabricator.Phabricator(token=self.conduit_token, host=self.host)
        phab.update_interfaces()
        return phab

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

    def pull(self):
        self.get_revisions()
        # TODO: match diffs (from build logs) with revisions

    def get_revisions(self):
        from_date = int(datetime.date(year=2019, month=10, day=1).strftime('%s'))
        data = []
        cursor = {
            'limit': 100
        }
        constraints = {
            'createdStart': from_date
        }
        after = None
        while True:
            revisions = self.phab.differential.revision.search(
                constraints=constraints, after=after)
            data.extend(revisions.response['data'])
            after = revisions.response['cursor']['after']
            if after is None:
                break
        print('Number of revisions:', len(data))
        if not os.path.exists('tmp'):
            os.mkdir('tmp')
        with open('tmp/revisions.json', 'w') as json_file:
            json.dump(data, json_file)


if __name__ == '__main__':
    puller = PhabBuildPuller()
    puller.pull()