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

from phabtalk.phabtalk import PhabTalk
from buildkite_utils import format_url, BuildkiteApi, strip_emojis
import test_results_report
from benedict import benedict


def get_failed_jobs(build: benedict) -> []:
    failed_jobs = []
    for j in build.get('jobs', []):
        j = benedict(j)
        if j.get('state') == 'failed' and j.get('name'):
            failed_jobs.append(j.get('name'))
    return failed_jobs


def process_unit_test_reports(bk: BuildkiteApi, build: benedict, prefix: str) -> []:
    failed_tests = []
    for job in build.get('jobs', []):
        job = benedict(job)
        if job.get('state') != 'failed' or job.get('type') != 'script':
            # Job must run scripts and fail to be considered.
            # Recursive pipeline triggers are not processed at the moment.
            continue
        artifacts_url = job.get('artifacts_url')
        if artifacts_url is None:
            continue
        artifacts = bk.get(artifacts_url).json()
        for a in artifacts:
            a = benedict(a)
            if not a.get('filename').endswith('test-results.xml') or not a.get('download_url'):
                continue
            content = bk.get(a.get('download_url')).content
            ctx = strip_emojis(prefix + ' ' + job.get('name', build.get('pipeline.name')))
            failed_tests.extend(test_results_report.parse_failures(content, ctx))
    return failed_tests


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--log-level', type=str, default='INFO')
    args = parser.parse_args()
    logging.basicConfig(level=args.log_level, format='%(levelname)-7s %(message)s')
    ph_buildable_diff = os.getenv('ph_buildable_diff')
    ph_target_phid = os.getenv('ph_target_phid')
    if ph_target_phid is None:
        logging.warning('ph_target_phid is not specified. Will not update the build status in Phabricator')
        exit(0)
    phabtalk = PhabTalk(os.getenv('CONDUIT_TOKEN'), dry_run_updates=(os.getenv('ph_dry_run_report') is not None))
    report_success = False  # for try block
    failed_tests = []
    try:
        bk = BuildkiteApi(os.getenv("BUILDKITE_API_TOKEN"), os.getenv("BUILDKITE_ORGANIZATION_SLUG"))
        build = bk.get_build(os.getenv("BUILDKITE_PIPELINE_SLUG"), os.getenv("BUILDKITE_BUILD_NUMBER"))
        success = True
        failed_tests = process_unit_test_reports(bk, build, '')
        for i, job in enumerate(build.get('jobs', [])):
            job = benedict(job)
            job_web_url = job.get('web_url', os.getenv('BUILDKITE_BUILD_URL', ''))
            logging.info(f'{job.get("id")} {job.get("name")} state {job.get("state")}')
            job_state = job.get('state')
            if job.get('type') == 'waiter':
                continue
            if job_state != 'passed' and job_state != 'failed':
                # Current and irrelevant steps.
                continue
            if job_state == 'passed' and i == 0:
                # Skip successful first step as we assume it to be a pipeline setup
                continue
            name = job.get('name')
            if job.get('type') == 'trigger':
                job_web_url = job.get('triggered_build.web_url', job_web_url)
                triggered_url = job.get('triggered_build.url')
                if triggered_url != '':
                    sub_build = benedict(bk.get(triggered_url).json())
                    name = name or sub_build.get('pipeline.name')
                    failed_steps = get_failed_jobs(sub_build)
                    failed_tests.extend(process_unit_test_reports(bk, sub_build, name))
                    if job_state == 'failed' and failed_steps:
                        name = f"{name} ({', '.join(failed_steps[:2])}{', ...' if len(failed_steps) > 2 else ''})"
            name = strip_emojis(name) or 'unknown'
            phabtalk.maybe_add_url_artifact(ph_target_phid, job_web_url, f"{name} {job_state}")
            if job_state == 'failed':
                success = False
        report_success = success  # Must be last before finally: block to report errors in this script.
    finally:
        build_url = f'https://reviews.llvm.org/harbormaster/build/{os.getenv("ph_build_id")}'
        print(f'Reporting results to Phabricator build {format_url(build_url)}', flush=True)
        phabtalk.update_build_status(ph_target_phid, False, report_success, {}, failed_tests)
