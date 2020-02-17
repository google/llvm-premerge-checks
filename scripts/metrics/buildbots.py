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

from datetime import date
import requests
import datetime
from google.cloud import monitoring_v3

BASE_URL = 'http://lab.llvm.org:8011/json/builders'
GCP_PROJECT_ID = 'llvm-premerge-checks'

class BuildStats:
    """Build statistics.
    
    Plain data object.
    """

    successful = 0  # type: int
    failed = 0      # type: int

    def __init__(self, successful:int = 0, failed:int = 0):
        self.successful = successful
        self.failed = failed

    def add(self, success: bool):
        if success:
            self.successful += 1
        else:
            self.failed += 1

    @property
    def total(self) -> int:
        return self.successful + self.failed

    @property
    def percent_failed(self) -> float:
        return 100.0 * self.failed / self.total

    def __add__(self, other: "BuildStats") -> "BuildStats":
        return BuildStats(
            self.successful + other.successful,
            self.failed + other.failed)

    def __str__(self) -> str:
        result = [
            'successful: {}'.format(self.successful),
            'failed: {}'.format(self.failed),
            'total: {}'.format(self.total),
            '% failed: {:0.1f}'.format(self.percent_failed),
        ]
        return '\n'.join(result)


def get_buildbot_stats(time_window : datetime.datetime) -> BuildStats:
    """Get the statistics for the all builders."""
    print('getting list of builders...')
    stats = BuildStats()
    for builder in requests.get(BASE_URL).json().keys():
        # TODO: maybe filter the builds to the ones we care about
        stats += get_builder_stats(builder, time_window )
    return stats


def get_builder_stats(builder: str, time_window: datetime.datetime) -> BuildStats:
    """Get the statistics for one builder."""
    print('Gettings builds for {}...'.format(builder))
    # TODO: can we limit the data we're requesting?
    url = '{}/{}/builds/_all'.format(BASE_URL, builder)
    stats = BuildStats()
    for build, results in requests.get(url).json().items():        
        start_time = datetime.datetime.fromtimestamp(float(results['times'][0]))
        if start_time < time_window:
            continue
        successful = results['text'] == ['build', 'successful']
        stats.add(successful)
    return stats


def gcp_create_metric_descriptor(project_id: str):
    """Create metric descriptors on Stackdriver.
    
    Re-creating these with every call is fine."""
    client = monitoring_v3.MetricServiceClient()
    project_name = client.project_path(project_id)

    for desc_type, desc_desc in [
        ["buildbots_percent_failed", "Percentage of failed builds"],
        ["buildbots_builds_successful", "Number of successful builds in the last 24h."],
        ["buildbots_builds_failed", "Number of failed builds in the last 24h."],
        ["buildbots_builds_total", "Total number of builds in the last 24h."],
    ]:

        descriptor = monitoring_v3.types.MetricDescriptor()
        descriptor.type = 'custom.googleapis.com/buildbots_{}'.format(desc_type)
        descriptor.metric_kind = (
            monitoring_v3.enums.MetricDescriptor.MetricKind.GAUGE)
        descriptor.value_type = (
            monitoring_v3.enums.MetricDescriptor.ValueType.DOUBLE)
        descriptor.description = desc_desc
        descriptor = client.create_metric_descriptor(project_name, descriptor)
        print('Created {}.'.format(descriptor.name))


def gcp_write_data(project_id: str, stats: BuildStats):
    """Upload metrics to Stackdriver."""
    client = monitoring_v3.MetricServiceClient()
    project_name = client.project_path(project_id)
    now = datetime.datetime.now()

    for desc_type, value in [
        ["buildbots_percent_failed", stats.percent_failed],
        ["buildbots_builds_successful", stats.successful],
        ["buildbots_builds_failed", stats.failed],
        ["buildbots_builds_total", stats.total],
    ]:
        series = monitoring_v3.types.TimeSeries()
        series.metric.type = 'custom.googleapis.com/buildbots_{}'.format(desc_type)
        series.resource.type = 'global'
        point = series.points.add()
        point.value.double_value = value
        point.interval.end_time.seconds = int(now.timestamp())
        client.create_time_series(project_name, [series])

if __name__ == '__main__':
    gcp_create_metric_descriptor(GCP_PROJECT_ID)
    stats = get_buildbot_stats(
        datetime.datetime.now() - datetime.timedelta(hours=24))
    gcp_write_data(GCP_PROJECT_ID, stats)
    print(stats)
