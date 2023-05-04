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
from typing import Any, Optional
from lxml import etree
from phabtalk.phabtalk import Report, Step


def run(working_dir: str, test_results: str, step: Optional[Step], report: Optional[Report]):
    if report is None:
        report = Report()  # For debugging.
    if step is None:
        step = Step()
    path = os.path.join(working_dir, test_results)
    if not os.path.exists(path):
        logging.error(f'{path} is not found')
        step.success = False
        return
    try:
        success = True
        root_node = etree.parse(path)
        for test_case in root_node.xpath('//testcase'):
            test_result = 'pass'
            if test_case.find('failure') is not None:
                test_result = 'fail'
            if test_case.find('skipped') is not None:
                test_result = 'skip'
            report.test_stats[test_result] += 1
            if test_result == 'fail':
                success = False
                failure = test_case.find('failure')
                test_result = {
                    'name': test_case.attrib['name'],
                    'namespace': test_case.attrib['classname'],
                    'result': test_result,
                    'duration': float(test_case.attrib['time']),
                    'details': failure.text
                }
                report.unit.append(test_result)

        msg = f'{report.test_stats["pass"]} tests passed, {report.test_stats["fail"]} failed and ' \
              f'{report.test_stats["skip"]} were skipped.\n'
        if not success:
            step.success = False
            for test_case in report.unit:
                if test_case['result'] == 'fail':
                    msg += f'{test_case["namespace"]}/{test_case["name"]}\n'
    except Exception as e:
        logging.error(e)
        step.success = False

    logging.debug(f'report: {report}')
    logging.debug(f'step: {step}')


def parse_failures(test_xml: bytes, context: str) -> []:
    failed_cases = []
    root_node = etree.fromstring(test_xml)
    for test_case in root_node.xpath('//testcase'):
        failure = test_case.find('failure')
        if failure is None:
            continue
        failed_cases.append({
            'engine': context,
            'name': test_case.attrib['name'],
            'namespace': test_case.attrib['classname'],
            'result': 'fail',
            'duration': float(test_case.attrib['time']),
            'details': failure.text,
        })
    return failed_cases

def add_context_prefix(tests: list[Any], prefix: str) -> list[Any]:
  for c in tests:
    c['engine'] = prefix + c['engine']
  return tests

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Processes results from xml report')
    parser.add_argument('test-report', default='build/test-results.xml')
    parser.add_argument('--log-level', type=str, default='INFO')
    args = parser.parse_args()
    logging.basicConfig(level=args.log_level)
    run(os.getcwd(), args.test_report, None, None)
