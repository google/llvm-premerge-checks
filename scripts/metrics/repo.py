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

import datetime
from time import timezone
import git
from typing import Dict
from google.cloud import monitoring_v3

from datetime import tzinfo

GCP_PROJECT_ID = 'llvm-premerge-checks'

class RepoStats:

    def __init__(self):
        self.commits = 0  # type: int
        self.reverts = 0  # type: int

    @property
    def percent_reverted(self) -> float:
        return 100.0 * self.reverts / self.commits

    def __str__(self):
        return "\n".join([
            "commits: {}".format(self.commits),
            "reverts: {}".format(self.reverts),
            "percent reverted: {:0.1f}".format(self.percent_reverted),
            ])

def get_reverts_per_day(repo_path: str, max_age: datetime.datetime) -> RepoStats:
    stats = RepoStats()
    repo = git.Repo(repo_path)
    repo.git.fetch()
    for commit in repo.iter_commits('master'):
        if commit.committed_datetime < max_age:
            break
        stats.commits += 1
        if commit.summary.startswith('Revert'):
            stats.reverts += 1
    return stats


def gcp_write_data(project_id: str, stats: RepoStats, now:datetime.datetime):
    """Upload metrics to Stackdriver."""
    client = monitoring_v3.MetricServiceClient()
    project_name = client.project_path(project_id)

    for desc_type, value in [
        ["reverts", stats.reverts],
        ["commits", stats.commits],
        ["percent_reverted", stats.percent_reverted],
    ]:
        series = monitoring_v3.types.TimeSeries()
        series.metric.type = 'custom.googleapis.com/repository_{}'.format(desc_type)
        series.resource.type = 'global'
        point = series.points.add()
        point.value.double_value = value
        point.interval.end_time.seconds = int(now.timestamp())
        client.create_time_series(project_name, [series])


if __name__ == '__main__':
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    max_age = now - datetime.timedelta(days=1)
    # TODO: make path configurable
    stats = get_reverts_per_day('~/git/llvm-project', max_age)
    print(stats)
    gcp_write_data(GCP_PROJECT_ID, stats, now)