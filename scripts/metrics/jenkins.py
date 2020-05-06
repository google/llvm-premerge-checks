#!/usr/bin/env python3

import csv
import datetime
import hashlib
import json
import numpy
import requests
import os
import sys
from typing import Optional, List, Dict
from urllib.parse import urljoin


class Stage:

    def __init__(self, stage_dict: Dict):
        self.name = stage_dict['name']
        self.success = stage_dict['status'].lower() == 'success'
        self.start_time = datetime.datetime.fromtimestamp(stage_dict['startTimeMillis']/1000)
        self.duration = datetime.timedelta(milliseconds=stage_dict['durationMillis'])


class Build:

    def __init__(self, job_name: str, build_dict: Dict):
        self.job_name = job_name
        self.number = build_dict['number']
        self.result = build_dict['result']
        self.start_time = datetime.datetime.fromtimestamp(build_dict['timestamp']/1000)
        self.duration = datetime.timedelta(milliseconds=build_dict['duration'])
        self.stages = []  # type: List[Stage]

    @property
    def hour(self) -> datetime.datetime:
        return datetime.datetime(
            year=self.start_time.year,
            month=self.start_time.month,
            day=self.start_time.day,
            hour=self.start_time.hour,
        )

    @property
    def day(self) -> datetime.datetime:
        return datetime.datetime(
            year=self.start_time.year,
            month=self.start_time.month,
            day=self.start_time.day,
        )

    def update_from_wfdata(self, wfdata: Dict):
        self.stages = [Stage(s) for s in wfdata['stages']]


class JenkinsStatsReader:
    _TMP_DIR = 'tmp/jenkins'

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
        jobnames = self.fetch_jobsnames()
        print('Found {} jobs: {}'.format(len(jobnames), jobnames))
        self.get_builds(jobnames)
        self.get_workflow_data()
        self.create_statistics('hour')
        self.create_statistics('day')

    def cached_get(self, url) -> Dict:
        m = hashlib.sha256()
        m.update(url.encode('utf-8'))
        filename = m.digest().hex()
        cache_file = os.path.join(self._TMP_DIR, filename)
        if os.path.isfile(cache_file):
            with open(cache_file, 'r') as json_file:
                data = json.load(json_file)
            return data

        response = self._session.get(urljoin(self.jenkins_url, url))
        if response.status_code != 200:
            raise IOError('Could not read data from {}:\n{}'.format(url, response.text))
        os.makedirs(self._TMP_DIR, exist_ok=True)
        with open(cache_file, 'w') as jenkins_data_file:
            jenkins_data_file.write(response.text)
        return response.json()

    def fetch_jobsnames(self) -> List[str]:
        data = self.cached_get('api/json?tree=jobs[name]')
        return [job['name'] for job in data['jobs']]

    def get_builds(self, job_names):
        for job_name in job_names:
            print('Gettings builds for: {}'.format(job_name))
            build_data = self.cached_get('job/{}/api/json?tree=allBuilds[number,result,duration,timestamp,executor]'.format(job_name))
            self.builds[job_name] = [Build(job_name, b) for b in build_data['allBuilds']]
            print('{} has {} builds'.format(job_name, len(self.builds[job_name])))

    def get_workflow_data(self):
        for job_name, builds in self.builds.items():
            for i, build in enumerate(builds):
                wfdata = self.cached_get('job/{}/{}/wfapi/'.format(job_name, build.number))
                build.update_from_wfdata(wfdata)
                sys.stdout.write('\r{} [{}/{}]'.format(job_name, i, len(builds)))
                sys.stdout.flush()

    def create_statistics(self, group_by: str):
        for job_name, builds in self.builds.items():
            print('Writing data for {}'.format(job_name))
            # TODO: add success/failure rates
            fieldnames = ['date', '# builds', 'median duration', 'p90 duration', 'p95 duration', 'max duration']
            csv_file = open('tmp/jenkins_{}_{}.csv'.format(job_name, group_by), 'w')
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames, dialect=csv.excel)
            writer.writeheader()
            build_hist = {}
            for build in builds:
                build_hist.setdefault(getattr(build, group_by), []).append(build)

            for key in sorted(build_hist.keys()):
                builds = build_hist[key]   # type: List[Build]
                durations = numpy.array([b.duration.seconds for b in builds])
                writer.writerow({
                    'date': key,
                    '# builds': len(builds),
                    'median duration': numpy.median(durations)/60,
                    'p90 duration':  numpy.percentile(durations, 90)/60,
                    'p95 duration': numpy.percentile(durations, 95)/60,
                    'max duration': numpy.max(durations)/60,
                })


if __name__ == '__main__':
    jsr = JenkinsStatsReader()
    jsr.get_data()
