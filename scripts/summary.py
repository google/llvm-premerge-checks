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

import argparse
import logging
import os
from typing import Any, Tuple

from phabtalk.phabtalk import PhabTalk
from buildkite_utils import format_url, BuildkiteApi, strip_emojis
import xunit_utils
from command_utils import get_env_or_die
from benedict import benedict
from dataclasses import dataclass


def get_failed_jobs(build: benedict) -> []:
    failed_jobs = []
    for j in build.get('jobs', []):
        j = benedict(j)
        if j.get('state') == 'failed' and j.get('name'):
            failed_jobs.append(j.get('name'))
    return failed_jobs


@dataclass
class jobResult:
    name: str
    url: str
    sub: list
    success: bool
    tests: list

# Returns list of jobs in the build and success flag.
def process_build(bk: BuildkiteApi, build: benedict) -> Tuple[list[jobResult], bool]:
    logging.info(f"Processing build {build.get('id')} {build.get('pipeline.name')}. All jobs:")
    for job in build.get('jobs', []):
        logging.info(f'job ID={job.get("id")} NAME={job.get("name")} type={job.get("type")} state={job.get("state")}')
    success = True
    result = []
    for job in build.get('jobs', []):
        job = benedict(job)
        job_type = job.get('type')
        logging.info(f'Processing job ID={job.get("id")}')
        if job.get('id') == os.getenv("BUILDKITE_JOB_ID"):
            logging.info("job ID matches current job, ignoring")
            continue
        job_state = job.get('state')
        if job_type == 'waiter':
            logging.info('job type is "waiter", ignoring')
            continue
        name = job.get('name')
        if (name is None) or (strip_emojis(name).strip() == ''):
            name = f"({job.get('type')})"
        logging.info(f"name {name}")
        name = strip_emojis(name)
        j = jobResult(
            name=name,
            sub=[],
            success=job_state=='passed',
            tests=fetch_job_unit_tests(job),
            url=job.get('web_url',''))
        if job.get('type') == 'trigger':
            triggered_url = job.get('triggered_build.url')
            logging.info(f'processing a trigger build from {triggered_url}')
            if triggered_url != '':
                sub_build = benedict(bk.get(triggered_url).json())
                j.name = sub_build.get('pipeline.name')
                j.url = sub_build.get('web_url')
                j.sub, s = process_build(bk, sub_build)
                j.success = j.success and s
        result.append(j)
        success = success and j.success
    return [result, success]

# Returns a list of failed tests from a failed script job.
def fetch_job_unit_tests(job: benedict) -> list[Any]:
    if job.get('state') != 'failed' or job.get('type') != 'script':
        logging.info(f"skipping job with state {job.get('state')} and type {job.get('type')}, only failed scripts are considered")
        return []
    artifacts_url = job.get('artifacts_url')
    if artifacts_url is None:
        logging.warning('job has not artifacts')
        return []
    artifacts = bk.get(artifacts_url).json()
    for a in artifacts:
        a = benedict(a)
        if not a.get('filename').endswith('test-results.xml') or not a.get('download_url'):
            continue
        content = bk.get(a.get('download_url')).content
        ctx = strip_emojis(job.get('name', build.get('pipeline.name')))
        return xunit_utils.parse_failures(content, ctx)
    logging.info('file test-results.xml not found')
    return []

def print_jobs(jobs: list[jobResult], pad: str):
    for j in jobs:
        print(f"{pad} {j.name} {j.success}")
        print_jobs(j.sub, pad + '  ')

# Returns a flat list of job results. Sub jobs get a prefix of a parent one.
def flatten_jobs(jobs: list[jobResult], prefix: str) -> Tuple[list[jobResult], list[Any]]:
    r = []
    t = []
    for j in jobs:
        j.name = prefix + j.name
        t.extend(xunit_utils.add_context_prefix(j.tests, prefix))
        r.append(j)
        sr, st = flatten_jobs(j.sub, f"{j.name} - ")
        r.extend(sr)
        t.extend(st)
    return [r, t]

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--log-level', type=str, default='INFO')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()
    logging.basicConfig(level=args.log_level, format='%(levelname)-7s %(message)s')
    bk_api_token = get_env_or_die('BUILDKITE_API_TOKEN')
    bk_pipeline_slug = get_env_or_die('BUILDKITE_PIPELINE_SLUG')
    bk_organization_slug = get_env_or_die("BUILDKITE_ORGANIZATION_SLUG")
    bk_build_number = get_env_or_die("BUILDKITE_BUILD_NUMBER")
    dry_run=os.getenv('ph_dry_run_report') is not None
    if dry_run:
      logging.info('running in dry-run mode, not exchanging with phabricator')
    ph_buildable_diff = os.getenv('ph_buildable_diff')
    conduit_token = get_env_or_die('CONDUIT_TOKEN')
    ph_target_phid = 'ph_target_phid'
    if not dry_run:
        ph_target_phid = get_env_or_die('ph_target_phid')
    phabtalk = PhabTalk(conduit_token, dry_run_updates=dry_run)
    report_success = False  # for try block
    failed_tests = []
    try:
        bk = BuildkiteApi(bk_api_token, bk_organization_slug)
        # Build type is https://buildkite.com/docs/apis/rest-api/builds#get-a-build.
        build = bk.get_build(bk_pipeline_slug, bk_build_number)
        jobs, success = process_build(bk, build)
        jobs, failed_tests = flatten_jobs(jobs, '')
        if args.debug:
            print_jobs(jobs, '')
            for t in failed_tests:
                t['details'] = ''
        for j in jobs:
            if not j.success:
                phabtalk.maybe_add_url_artifact(ph_target_phid, j.url, j.name)
        report_success = success
    finally:
        build_url = f'https://reviews.llvm.org/harbormaster/build/{os.getenv("ph_build_id")}'
        print(f'Reporting results to Phabricator build {format_url(build_url)}', flush=True)
        phabtalk.update_build_status(ph_target_phid, False, report_success, {}, failed_tests)
