#!/usr/bin/env python3

import requests
from typing import Optional, List, Dict
import json
import os
from urllib.parse import urljoin
import datetime
import numpy
import csv

class Build:

    def __init__(self, job_name: str, build_dict: Dict):
        self.job_name = job_name
        self.number = build_dict['number']
        self.result = build_dict['result']
        self.start_time = datetime.datetime.fromtimestamp(build_dict['timestamp']/1000)
        self.duration = datetime.timedelta(milliseconds=build_dict['duration'])

    @property
    def day(self) -> datetime.datetime:
        return datetime.datetime(
            year=self.start_time.year,
            month=self.start_time.month,
            day=self.start_time.day,
            hour=self.start_time.hour,
        )


class JenkinsStatsReader:

    _JENKINS_DAT_FILE = 'tmp/jenkins.json'

    def __init__(self):
        self.username = None  # type: Optional[str]
        self.password = None  # type: Optional[str]
        self.jenkins_url = None  # type: Optional[str]
        self.jobs = []  # type: List[str]
        self.builds = {}  # type: Dict[str, List[Build]]
        self._read_config()
        self._session = requests.session()
        self._session.auth = (self.username, self.password)

    def _read_config(self, credential_path='~/.llvm-premerge-checks/jenkins-creds.json'):
        with open(os.path.expanduser(credential_path)) as credential_file:
            config = json.load(credential_file)
        self.username = config['username']
        self.password = config['password']
        self.jenkins_url = config['jenkins_url']

    @property
    def job_names(self) -> List[str]:
        return self.builds.keys()

    def get_data(self):
        if not os.path.isfile(self._JENKINS_DAT_FILE):
            self.fetch_data()
        self.parse_data()
        self.create_day_statistics()

    def fetch_data(self):
        response = self._session.get(
            urljoin(self.jenkins_url, 'api/json?tree=jobs[name,url,allBuilds[number,result,duration,url,timestamp]]'))
        with open(self._JENKINS_DAT_FILE, 'w') as jenkins_data_file:
            json.dump(response.json(), jenkins_data_file)

    def parse_data(self):
        with open(self._JENKINS_DAT_FILE) as jenkins_data_file:
            build_data = json.load(jenkins_data_file)
        for job in build_data['jobs']:
            job_name = job['name']
            self.builds[job_name] = [Build(job_name, b) for b in job['allBuilds']]
            print('{} has {} builds'.format(job_name, len(self.builds[job_name])))

    def create_day_statistics(self):
        build_day = {}
        # only look at Phab
        for job_name, builds in self.builds.items():
            print('Writing data for {}'.format(job_name))
            fieldnames = ['date', '# builds', 'median duration', 'p90 duration', 'p95 duration', 'max duration']
            csv_file = open('tmp/jenkins_{}.csv'.format(job_name), 'w')
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames, dialect=csv.excel)
            writer.writeheader()
            for build in builds:
                build_day.setdefault(build.day, []).append(build)

            for day in sorted(build_day.keys()):
                builds = build_day[day]   # type: List[Build]
                durations = numpy.array([b.duration.seconds for b in builds])
                writer.writerow({
                    'date': day,
                    '# builds': len(builds),
                    'median duration': numpy.median(durations)/60,
                    'p90 duration':  numpy.percentile(durations, 90)/60,
                    'p95 duration': numpy.percentile(durations, 95)/60,
                    'max duration': numpy.max(durations)/60,
                })


if __name__ == '__main__':
    jsr = JenkinsStatsReader()
    jsr.get_data()
