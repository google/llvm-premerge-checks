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

# Get data on Revisions and builds from Phabricator

import phabricator
import json
import os
import datetime
from typing import Dict, List, Optional
import csv
import time
import socket
import git
import argparse

# PHIDs of build plans used for pre-merge testing
# FIXME: how do you get these?
_PRE_MERGE_PHIDs = ['PHID-HMCP-bfkbtacsszhg3feydpo6',  # beta testers
                    'PHID-HMCP-qbviyekvgirhhhvkzpsn',   # public pre-merge tests
                    'PHID-HMCP-p2oc4ocen3l2yzymvg2l',
                    ]

# query all data after this date
START_DATE = datetime.date(year=2019, month=10, day=1)

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
        self.diffs = []  # type: List['Diff']

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

    @property
    def repository_phid(self) -> str:
        return self.revision_dict['fields']['repositoryPHID']

    @property
    def diff_phid(self) -> str:
        return self.revision_dict['fields']['diffPHID']

    @property
    def all_diffs_have_refs(self) -> bool:
        return not any(not d.has_refs for d in self.diffs)

    @property
    def day(self) -> datetime.date:
        return datetime.date.fromtimestamp(self.created_date)

    @property
    def week(self) -> str:
        day = self.day
        return'{}-w{:02d}'.format(day.year, day.isocalendar()[1])


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
        result = self.buildplan_phid in _PRE_MERGE_PHIDs
        if not result:
            print(self.buildplan_phid)
        return result


class Diff(PhabResponse):

    def __init__(self, revision_dict):
        super().__init__(revision_dict)
        self.revision = None  # type: Optional[Revision]

    @property
    def revison_phid(self) -> str:
        return self.revision_dict['fields']['revisionPHID']

    @property
    def _refs(self) -> List:
        return self.revision_dict['fields']['refs']

    @property
    def has_refs(self) -> bool:
        return len(self._refs) > 0

    @property
    def base_revision(self) -> str:
        for ref in self._refs:
            if ref['type'] == 'base':
                return ref['identifier']
        return None

    @property
    def base_branch(self) -> str:
        for ref in self._refs:
            if ref['type'] == 'branch':
                return ref['name']
        return None

    @property
    def dateCreated(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(self.revision_dict['fields']['dateCreated'])

class PhabBuildPuller:
    # files/folder for sotring temporary results
    _TMP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'tmp'))
    _REVISION_FILE = os.path.join(_TMP_DIR, 'phab-revisions.json')
    _BUILDABLE_FILE = os.path.join(_TMP_DIR, 'phab-buildables.json')
    _BUILD_FILE = os.path.join(_TMP_DIR, 'phab-build.json')
    _DIFF_FILE = os.path.join(_TMP_DIR, 'phab-diffs.json')
    _PHAB_WEEKLY_METRICS_FILE = os.path.join(_TMP_DIR, 'phabricator_{}.csv')

    def __init__(self, repo_path: str):
        self.conduit_token = None
        self.host = None
        self.phab = self._create_phab()
        self._repo_path = repo_path  # type: str
        self.revisions = {}  # type: Dict[str, Revision]
        self.buildables = {}  # type: Dict[str, Buildable]
        self.builds = {}  # type: Dict[str, Build]
        self.diffs = {}  # type: Dict[str, Diff]

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

    def run(self):
        if not os.path.exists(self._TMP_DIR):
            os.mkdir(self._TMP_DIR)
        if not os.path.isfile(self._REVISION_FILE):
            self.get_revisions()
        self.parse_revisions()
        if not os.path.isfile(self._BUILDABLE_FILE):
            self.get_buildables()
        self.parse_buildables()
        if not os.path.isfile(self._BUILD_FILE):
            self.get_builds()
        self.parse_builds()
        if not os.path.isfile(self._DIFF_FILE):
            self.get_diffs()
        self.parse_diffs()
        self.link_objects()
        self.compute_metrics('day', lambda r: r.day)
        self.compute_metrics('week', lambda r: r.week)
        self.count_base_revisions()
        self.match_base_revisions_with_repo(self._repo_path)

    def get_revisions(self):
        print('Downloading revisions starting...')
        from_date = int(START_DATE.strftime('%s'))
        data = []
        constraints = {
            'createdStart': from_date
        }
        # FIXME: lots of code duplication around pagination and error handling.
        # find a way to separate this into a function.
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
                containerPHIDs=[r.phid for r in self.revisions.values()], after=after)
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
            'buildables': [r.phid for r in self.buildables.values()]
        }
        after = None
        while True:
            # retry on timeouts
            fail_count = 0
            while True:
                try: 
                    revisions = self.phab.harbormaster.build.search(
                        constraints=constraints, after=after)
                except socket.timeout:
                    fail_count +=1
                    if fail_count > 5:
                        raise
                    time.sleep(10)
                    continue
                break
            data.extend(revisions.response['data'])
            print('{} builds...'.format(len(data)))
            after = revisions.response['cursor']['after']
            if after is None:
                break
        print('Number of buildables:', len(data))
        with open(self._BUILD_FILE, 'w') as json_file:
            json.dump(data, json_file)

    def get_diffs(self):
        print('Downloading diffs...')
        data = []
        constraints = {
            'revisionPHIDs': [r.phid for r in self.revisions.values()]
        }
        after = None
        while True:
            # retry on timeouts
            fail_count = 0
            while True:
                try: 
                    diffs = self.phab.differential.diff.search(
                        constraints=constraints, after=after)
                except socket.timeout:
                    fail_count +=1
                    if fail_count > 5:
                        raise
                    time.sleep(10)
                    continue
                break
            data.extend(diffs.response['data'])
            print('{} diffs...'.format(len(data)))
            after = diffs.response['cursor']['after']
            if after is None:
                break
        print('Number of diffs:', len(data))
        with open(self._DIFF_FILE, 'w') as json_file:
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

    def parse_diffs(self):
        with open(self._DIFF_FILE) as diff_file:
            diff_dict = json.load(diff_file)
        self.diffs = {d.phid: d for d in (Diff(x) for x in diff_dict)}
        print('Parsed {} diffs.'.format(len(self.diffs)))

    def link_objects(self):
        for build in (b for b in self.builds.values()):
            buildable = self.buildables[build.buildable_phid]
            build.buildable = buildable
            buildable.builds.append(build)

        for buildable in self.buildables.values():
            revision = self.revisions[buildable.revison_phid]
            revision.buildables.append(buildable)
            buildable.revision = revision

        for diff in self.diffs.values():
            revision = self.revisions[diff.revison_phid]
            revision.diffs.append(diff)
            diff.revision = revision

    def compute_metrics(self, name: str, group_function):
        print('Creating metrics for {}...'.format(name))
        group_dict = {}
        for revision in self.revisions.values():
            group_dict.setdefault(group_function(revision), []).append(revision)

        csv_file = open(self._PHAB_WEEKLY_METRICS_FILE.format(name), 'w')
        fieldnames = [name, '# revisions', '# tested revisions', '% tested revisions', '# untested revisions',
                      '# revisions without builds', '% revisions without builds', '# no repository set']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, dialect=csv.excel)
        writer.writeheader()
        for group in sorted(group_dict.keys()):
            revisions = group_dict[group]  # type: List[Revision]
            num_revisions = len(revisions)
            num_premt_revisions = len([r for r in revisions if r.was_premerge_tested])
            precentage_premt_revisions = 100.0 * num_premt_revisions / num_revisions
            num_no_build_triggered = len([r for r in revisions if len(r.builds) == 0])
            percent_no_build_triggered = 100.0 * num_no_build_triggered / num_revisions
            num_no_repo = len([r for r in revisions if r.repository_phid is None])
            writer.writerow({
                name: group,
                '# revisions': num_revisions,
                '# tested revisions': num_premt_revisions,
                '% tested revisions': precentage_premt_revisions,
                '# untested revisions': num_revisions - num_premt_revisions,
                '# revisions without builds': num_no_build_triggered,
                '% revisions without builds': percent_no_build_triggered,
                '# no repository set': num_no_repo,
            })

    def count_base_revisions(self):
        base_revisions = {}
        base_branches = {}
        for diff in self.diffs.values():
            base_revisions.setdefault(diff.base_revision, 0)
            base_revisions[diff.base_revision] += 1

            base_branches.setdefault(diff.base_branch, 0) 
            base_branches[diff.base_branch] +=1
        
        print(f'{len(self.diffs)} diffs are using {len(base_revisions)} different git base revisions.')
        print('The top 10 revisions and their usages are:')
        revisions = sorted( base_revisions.items(), key=lambda x: x[1] , reverse=True)
        for i in revisions[:10]:
            print(f'  commit {i[0]} was used {i[1]} times')
        print()
        print(f'{len(self.diffs)} diffs are using {len(base_branches)} different git base branches')
        branches = sorted( base_branches.items(), key=lambda x: x[1] , reverse=True)
        print('The top 10 branches and their usages are:')
        for i in branches[:10]:
            print(f'  branch {i[0]} was used {i[1]} times')
        print()

    def match_base_revisions_with_repo(self, repo_path: str):
        repo = git.Repo(repo_path)
        not_found = 0
        invalid_date = 0
        has_base_revision = 0
        for diff in self.diffs.values():
            revision = diff.base_revision
            if revision is None:
                continue
            has_base_revision += 1
            try:
                commit = repo.commit(revision)
            except (ValueError, git.BadName):
                not_found += 1
                continue
            commited_date = datetime.datetime.fromtimestamp(commit.committed_date)
            if commited_date > diff.dateCreated:
                invalid_date += 1
        print(f'Of the {has_base_revision} Diffs with base revision, the base revision was NOT found in the repo for {not_found} and ')
        print(f'{invalid_date} base revisions were used before being available upstream.')
        print(f'So {(not_found+invalid_date)/has_base_revision*100:0.2f} % of specified the base revisions were unusable.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('repo_path')
    args = parser.parse_args()
    puller = PhabBuildPuller(args.repo_path)
    puller.run()
