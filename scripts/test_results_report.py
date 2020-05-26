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
import os
import logging
from typing import Optional
from lxml import etree
from phabtalk.phabtalk import Report, CheckResult


def run(test_results, report: Optional[Report]):
    """Apply clang-format and return if no issues were found."""
    if report is None:
        report = Report()  # For debugging.
    if not os.path.exists(test_results):
        logging.warning(f'{test_results} not found')
        report.add_step('clang-format', CheckResult.UNKNOWN, 'test report is not found')
        return
    success = True
    root_node = etree.parse(test_results)
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

    msg = f'{report.test_stats["pass"]} tests passed, {report.test_stats["fail"]} failed and' \
          f'{report.test_stats["skip"]} were skipped.\n'
    if success:
        report.add_step('test results', CheckResult.SUCCESS, msg)
    else:
        for test_case in report.unit:
            if test_case['result'] == 'fail':
                msg += f'{test_case["namespace"]}/{test_case["name"]}\n'
        report.add_step('unit tests', CheckResult.FAILURE, msg)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Processes results from xml report')
    parser.add_argument('test_report', default='build/test-results.xml')
    parser.add_argument('--log-level', type=str, default='INFO')
    args = parser.parse_args()
    logging.basicConfig(level=args.log_level)
    run(args.test_report, None)
