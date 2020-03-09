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

# generate statistics on the llvm github repository

import csv
import datetime
import git
import re
import os
from typing import Dict, Optional, List
import random
import string

REVISION_REGEX = re.compile(
    r'^Differential Revision: https://reviews\.llvm\.org/(.*)$',
    re.MULTILINE)
REVERT_REGEX = re.compile(r'^Revert "(.+)"')


class MyCommit:

    SALT = ''.join(random.choices(
        string.ascii_lowercase + string.ascii_uppercase + string.digits, k=16))

    def __init__(self, commit: git.Commit):
        self.chash = commit.hexsha  # type: str
        self.author = hash(commit.author.email + MyCommit.SALT)  # type: int
        self.author_domain = commit.author.email.rsplit("@")[-1].lower()  # type: str
        self.commiter = hash(commit.committer.email.lower() + MyCommit.SALT)  # type:int
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

    @property
    def was_reverted(self) -> bool:
        return self.reverted_by is not None

    @property
    def was_reviewed(self) -> bool:
        return self.phab_revision is not None

    @property
    def is_revert(self) -> bool:
        return self.reverts is not None

    @property
    def week(self) -> str:
        return '{}-w{}'.format(self.date.year, self.date.isocalendar()[1])


class RepoStats:

    def __init__(self):
        self.commit_by_hash = dict()  # type: Dict[str, MyCommit]
        self.commit_by_summary = dict()  # type: Dict[str, List[MyCommit]]
        self.commit_by_week = dict()  # type: Dict[str, List[MyCommit]]
        self.commit_by_author = dict()  # type: Dict[int, List[MyCommit]]
        self.commit_by_author_domain = dict()  # type: Dict[int, List[MyCommit]]

    def parse_repo(self, git_dir: str, maxage: datetime.datetime):
        repo = git.Repo(git_dir)
        for commit in repo.iter_commits('master'):
            if commit.committed_datetime < maxage:
                break
            mycommit = MyCommit(commit)
            self.commit_by_hash[mycommit.chash] = mycommit
            self.commit_by_summary.setdefault(mycommit.summary, [])\
                .append(mycommit)
            self.commit_by_week.setdefault(mycommit.week, []).append(mycommit)
            self.commit_by_author.setdefault(mycommit.author, [])\
                .append(mycommit)
            self.commit_by_author_domain.setdefault(mycommit.author_domain, []) \
                .append(mycommit)

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
        fieldnames = ["week", "num_commits", "num_reverts", "percentage_reverts",
                      "num_reviewed", "percentage_reviewed"]
        csvfile = open('tmp/llvm-project-weekly.csv', 'w')
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames,
                                dialect=csv.excel)
        writer.writeheader()
        for week in sorted(self.commit_by_week.keys()):
            commits = self.commit_by_week[week]
            num_commits = len(commits)
            num_reverts = len([c for c in commits if c.is_revert])
            percentage_reverts = 100.0*num_reverts / num_commits
            num_reviewed = len([c for c in commits if c.was_reviewed])
            percentage_reviewed = 100*num_reviewed / (num_commits - num_reverts)
            writer.writerow({
                "week": week,
                "num_commits": num_commits,
                "num_reverts": num_reverts,
                "percentage_reverts": percentage_reverts,
                "num_reviewed": num_reviewed,
                "percentage_reviewed": percentage_reviewed,
            })

    def dump_overall_stats(self):
        num_commits = len(self.commit_by_hash)
        num_reverts = len([c for c in self.commit_by_hash.values()
                           if c.is_revert])
        print('Number of commits: {}'.format(num_commits))
        print('Number of reverts: {}'.format(num_reverts))
        print('percentage of reverts: {:0.2f}'.format(
            100*num_reverts / num_commits))

        num_reviewed = len([c for c in self.commit_by_hash.values()
                            if c.was_reviewed])
        print('Number of reviewed commits: {}'.format(num_reviewed))
        print('percentage of reviewed commits: {:0.2f}'.format(
            100*num_reviewed / num_commits))

        num_reviewed_reverted = len([c for c in self.commit_by_hash.values()
                                     if c.was_reviewed and c.was_reverted])
        num_not_reviewed_reverted = len([c for c in self.commit_by_hash.values()
                                         if not c.was_reviewed and
                                         c.was_reverted])
        print('Number of reviewed that were reverted: {}'.format(num_reviewed_reverted))
        print('Number of NOT reviewed that were reverted: {}'.format(num_not_reviewed_reverted))
        print('percentage of reviewed that were reverted: {:0.2f}'.format(
            100*num_reviewed_reverted / num_reviewed))
        print('percentage of NOT reviewed that were reverted: {:0.2f}'.format(
            100*num_not_reviewed_reverted / (num_commits-num_reviewed)))

        num_foreign_committer = len([c for c in self.commit_by_hash.values()
                                     if c.author != c.commiter])
        print('Number of commits where author != committer: {}'.format(
            num_foreign_committer))
        print('Percentage of commits where author != committer: {:0.2f}'.format(
            100*num_foreign_committer/num_commits))

    def dump_author_stats(self):
        print('Number of authors: {}'.format(len(self.commit_by_author)))
        fieldnames = ["author", "num_commits", "num_reverts", "percentage_reverts",
                      "num_reviewed", "percentage_reviewed"]
        csvfile = open('tmp/llvm-project-authors.csv', 'w')
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames,
                                dialect=csv.excel)
        writer.writeheader()
        for author, commits in self.commit_by_author.items():
            num_commits = len(commits)
            num_reverts = len([c for c in commits if c.was_reverted])
            percentage_reverts = 100 * num_reverts / num_commits
            num_reviewed = len([c for c in commits if c.was_reviewed])
            percentage_reviewed = 100*num_reviewed / num_commits
            writer.writerow({
                "author": author,
                "num_commits": num_commits,
                "num_reverts": num_reverts,
                "percentage_reverts": percentage_reverts,
                "num_reviewed": num_reviewed,
                "percentage_reviewed": percentage_reviewed,
            })

    def dump_author_domain_stats(self):
        print('Number of authors: {}'.format(len(self.commit_by_author)))
        fieldnames = ["author_domain", "num_commits", "num_committers"]
        csvfile = open('tmp/llvm-project-author_domains.csv', 'w')
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames,
                                dialect=csv.excel)
        writer.writeheader()
        for author_domain, commits in self.commit_by_author_domain.items():
            num_commits = len(commits)
            committers = set(c.author for c in commits)
            writer.writerow({
                "author_domain": author_domain,
                "num_commits": num_commits,
                "num_committers": len(committers),
            })


if __name__ == '__main__':
    max_age = datetime.datetime(year=2019, month=10, day=1,
                                tzinfo=datetime.timezone.utc)
    rs = RepoStats()
    # TODO: make the path configurable, and `git clone/pull`
    rs.parse_repo(os.path.expanduser('~/git/llvm-project'), max_age)
    rs.find_reverts()
    rs.dump_daily_stats()
    rs.dump_overall_stats()
    rs.dump_author_stats()
    rs.dump_author_domain_stats()
