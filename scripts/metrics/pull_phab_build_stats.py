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
from typing import Dict, List, Optional
import csv


_PRE_MERGE_PHID = 'PHID-HMCP-bfkbtacsszhg3feydpo6'


class PhabResponse:

    def __init__(self, revision_dict: Dict):
        self.revision_dict = revision_dict

    @property
    def id(self) -> str:
        return self.revision_dict['id']

    @property
    def phid(self) -> str:
        return self.revision_dict['phid']

    def __str__(self):
        return str(self.revision_dict)


class Revision(PhabResponse):

    def __init__(self, revision_dict):
        super().__init__(revision_dict)
        self.buildables = []  # type: List['Buildable']

    @property
    def status(self) -> str:
        return self.revision_dict['fields']['status']['value']

    @property
    def builds(self) -> List['Build']:
        builds = []
        for b in self.buildables:
            builds.extend(b.builds)
        return builds

    @property
    def created_date(self):
        return self.revision_dict['fields']['dateCreated']

    @property
    def was_premerge_tested(self) -> bool:
        return any((b.was_premerge_tested for b in self.builds))


class Buildable(PhabResponse):

    def __init__(self, revision_dict):
        super().__init__(revision_dict)
        self.builds = []  # type: List[Build]
        self.revision = None  # type: Optional[Revision]

    @property
    def diff_phid(self) -> str:
        return self.revision_dict['buildablePHID']

    @property
    def revison_phid(self) -> str:
        return self.revision_dict['containerPHID']


class Build(PhabResponse):

    def __init__(self, revision_dict):
        super().__init__(revision_dict)
        self.buildable = None  # type: Optional[Buildable]

    @property
    def buildable_phid(self) -> str:
        return self.revision_dict['fields']['buildablePHID']

    @property
    def buildplan_phid(self) -> str:
        return self.revision_dict['fields']['buildPlanPHID']

    @property
    def was_premerge_tested(self) -> bool:
        return self.buildplan_phid == _PRE_MERGE_PHID


class PhabBuildPuller:

    _REVISION_FILE = 'tmp/revisions.json'
    _BUILDABLE_FILE = 'tmp/buildables.json'
    _BUILD_FILE = 'tmp/build.json'
    _PHAB_WEEKLY_METRICS_FILE = 'tmp/phabricator_week.csv'

    def __init__(self):
        self.conduit_token = None
        self.host = None
        self.phab = self._create_phab()
        self.revisions = {}  # type: Dict[str,Revision]
        self.buildables = {}  # type: Dict[str,Buildable]
        self.builds = {}  # type: Dict[str,Build]

    def _create_phab(self) -> phabricator.Phabricator:
        phab = phabricator.Phabricator(token=self.conduit_token, host=self.host)
        #phab.update_interfaces()
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

    def run(self):
        if not os.path.exists('tmp'):
            os.mkdir('tmp')
        if not os.path.isfile(self._REVISION_FILE):
            self.get_revisions()
        self.parse_revisions()
        if not os.path.isfile(self._BUILDABLE_FILE):
            self.get_buildables()
        self.parse_buildables()
        if not os.path.isfile(self._BUILD_FILE):
            self.get_builds()
        self.parse_builds()
        self.link_objects()
        self.compute_metrics()

    def get_revisions(self):
        print('Downloading revisions starting...')
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
            print('{} revisions...'.format(len(data)))
            after = revisions.response['cursor']['after']
            if after is None:
                break
        print('Number of revisions:', len(data))
        with open(self._REVISION_FILE, 'w') as json_file:
            json.dump(data, json_file)

    def get_buildables(self):
        print('Downloading buildables...')
        data = []
        after = None
        while True:
            revisions = self.phab.harbormaster.querybuildables(
                containerPHIDs=[r.phid for r in self.revisions], after=after)
            data.extend(revisions.response['data'])
            print('{} buildables...'.format(len(data)))
            after = revisions.response['cursor']['after']
            if after is None:
                break
        print('Number of buildables:', len(data))
        with open(self._BUILDABLE_FILE, 'w') as json_file:
            json.dump(data, json_file)

    def get_builds(self):
        print('Downloading builds...')
        data = []
        constraints = {
            'buildables': [r.phid for r in self.buildables]
        }
        after = None
        while True:
            revisions = self.phab.harbormaster.build.search(
                constraints=constraints, after=after)
            data.extend(revisions.response['data'])
            print('{} builds...'.format(len(data)))
            after = revisions.response['cursor']['after']
            if after is None:
                break
        print('Number of buildables:', len(data))
        with open(self._BUILD_FILE, 'w') as json_file:
            json.dump(data, json_file)

    def parse_revisions(self):
        with open(self._REVISION_FILE) as revision_file:
            revision_dict = json.load(revision_file)
        self.revisions = {r.phid: r for r in (Revision(x) for x in revision_dict)}
        print('Parsed {} revisions.'.format(len(self.revisions)))

    def parse_buildables(self):
        with open(self._BUILDABLE_FILE) as buildables_file:
            buildable_dict = json.load(buildables_file)
        self.buildables = {b.phid: b for b in (Buildable(x) for x in buildable_dict)}
        print('Parsed {} buildables.'.format(len(self.buildables)))

    def parse_builds(self):
        with open(self._BUILD_FILE) as build_file:
            build_dict = json.load(build_file)
        self.builds = {b.phid: b for b in (Build(x) for x in build_dict)}
        print('Parsed {} builds.'.format(len(self.builds)))

    def link_objects(self):
        for build in (b for b in self.builds.values()):
            buildable = self.buildables[build.buildable_phid]
            build.buildable = buildable
            buildable.builds.append(build)

        for buildable in self.buildables.values():
            revision = self.revisions[buildable.revison_phid]
            revision.buildables.append(buildable)
            buildable.revision = revision

    def compute_metrics(self):
        days_dict = {}
        for revision in self.revisions.values():
            date = datetime.date.fromtimestamp(revision.created_date)
            week = '{}-w{}'.format(date.year, date.isocalendar()[1])
            days_dict.setdefault(week, []).append(revision)

        csv_file = open(self._PHAB_WEEKLY_METRICS_FILE, 'w')
        fieldnames = ['week', 'num_revisions', 'num_premt_revisions', 'precentage_premt_revisions', 'num_untested']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, dialect=csv.excel)
        writer.writeheader()
        for week in sorted(days_dict.keys()):
            revisions = days_dict[week]
            num_revisions = len(revisions)
            num_premt_revisions = len([r for r in revisions if r.was_premerge_tested])
            precentage_premt_revisions = 100.0 * num_premt_revisions / num_revisions
            writer.writerow({
                'week': week,
                'num_revisions': num_revisions,
                'num_premt_revisions': num_premt_revisions,
                'precentage_premt_revisions': precentage_premt_revisions,
                'num_untested': num_revisions - num_premt_revisions,
            })


if __name__ == '__main__':
    puller = PhabBuildPuller()
    puller.run()
