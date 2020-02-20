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

import csv
from collections import OrderedDict
import datetime
import git
import re
import os
from typing import Dict, Optional, List


REVISION_REGEX = re.compile(
    r'^Differential Revision: https://reviews\.llvm\.org/(.*)$',
    re.MULTILINE)
REVERT_REGEX = re.compile(r'^Revert "(.+)"')


class MyCommit:

    def __init__(self, commit: git.Commit):
        self.chash = commit.hexsha  # type: str
        self.author = commit.author.email  # type: str
        self.commiter = commit.committer.email  # type:str
        self.summary = commit.summary  # type: str
        self.date = datetime.datetime.fromtimestamp(
            commit.committed_date)  # type: datetime.datetime
        self.phab_revision = self._get_revision(commit)  # type: Optional[str]
        self.reverts = None   # type: Optional[MyCommit]
        self.reverted_by = None   # type: Optional[MyCommit]

    @staticmethod
    def _get_revision(commit: git.Commit) -> Optional[str]:
        m = REVISION_REGEX.search(commit.message)
        if m is None:
            return None
        return m.group(1)

    @property
    def day(self) -> datetime.date:
        return self.date.date()

    def reverts_summary(self) -> Optional[str]:
        m = REVERT_REGEX.search(self.summary)
        if m is None:
            return None
        return m.group(1)

    def __str__(self):
        return self.chash


class RepoStats:

    def __init__(self):
        self.commit_by_hash = dict()  # type: Dict[str, MyCommit]
        self.commit_by_summary = dict()  # type: Dict[str, List[MyCommit]]
        self.commit_by_day = dict()  # type: Dict[datetime.date, List[MyCommit]]

    def parse_repo(self, git_dir: str, maxage: datetime.datetime):
        repo = git.Repo(git_dir)
        for commit in repo.iter_commits('master'):
            if commit.committed_datetime < maxage:
                break
            mycommit = MyCommit(commit)
            self.commit_by_hash[mycommit.chash] = mycommit
            self.commit_by_summary.setdefault(mycommit.summary, [])
            self.commit_by_summary[mycommit.summary].append(mycommit)
            self.commit_by_day.setdefault(mycommit.day, [])
            self.commit_by_day[mycommit.day].append(mycommit)
        print('Read {} commits'.format(len(self.commit_by_hash)))

    def find_reverts(self):
        reverts = 0
        for commit in self.commit_by_hash.values():
            summary = commit.reverts_summary()
            if summary is None:
                continue
            if summary not in self.commit_by_summary:
                print('summary not found: {}'.format(summary))
                continue
            reverting_commit = self.commit_by_summary[summary][-1]
            commit.reverted_by = reverting_commit
            reverting_commit.reverts = commit
            reverts += 1
        print('Found {} reverts'.format(reverts))

    # TODO: try weekly stats, they might be smoother
    # https://stackoverflow.com/questions/2600775/how-to-get-week-number-in-python
    def dump_daily_stats(self):
        fieldnames = ["day", "num_commits", "num_reverts", "percentage_reverts",
                      "num_reviewed", "percentage_reviewed"]
        csvfile = open('llvm-project-daily.csv', 'w')
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames,
                                dialect=csv.excel)
        writer.writeheader()
        for day in sorted(self.commit_by_day.keys()):
            commits = self.commit_by_day[day]
            num_commits = len(commits)
            num_reverts = len([c for c in commits if c.reverts is not None])
            percentage_reverts = 100.0*num_reverts / num_commits
            num_reviewed = len([c for c in commits
                                if c.phab_revision is not None])
            percentage_reviewed = 100*num_reviewed / (num_commits - num_reverts)
            writer.writerow({
                "day": day,
                "num_commits": num_commits,
                "num_reverts": num_reverts,
                "percentage_reverts": percentage_reverts,
                "num_reviewed": num_reviewed,
                "percentage_reviewed": percentage_reviewed,
            })

    def dump_overall_stats(self):
        num_commits = len(self.commit_by_hash)
        num_reverts = len([c for c in self.commit_by_hash.values()
                           if c.reverted_by is not None])
        print('Number of commits: {}'.format(num_commits))
        print('Number of reverts: {}'.format(num_reverts))
        print('percentage of reverts: {:0.2f}'.format(
            100*num_reverts / num_commits))

        num_reviewed = len([c for c in self.commit_by_hash.values()
                            if c.phab_revision is not None])
        print('Number of reviewed commits: {}'.format(num_reviewed))
        print('percentage of reviewed commits: {:0.2f}'.format(
            100*num_reviewed / num_commits))


if __name__ == '__main__':
    max_age = datetime.datetime(year=2019, month=10, day=1,
                                tzinfo=datetime.timezone.utc)
    rs = RepoStats()
    rs.parse_repo(os.path.expanduser('~/git/llvm-project'), max_age)
    rs.find_reverts()
    rs.dump_daily_stats()
    rs.dump_overall_stats()
