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
"""Upload build results to Phabricator.

As I did not like the Jenkins plugin, we're using this script to upload the 
build status, a summary and the test reults to Phabricator."""

import argparse
import os
import time
from typing import Optional
from phabricator import Phabricator
import socket
from lxml import etree

class TestResults:

    def __init__(self):
        self.result_type = None  # type: str
        self.unit = []  #type: List
        self.test_stats = {
            'pass':0,
            'fail':0, 
            'skip':0
        }  # type: Dict[str, int]


class PhabTalk:
    """Talk to Phabricator to upload build results."""

    def __init__(self, token: Optional[str], host: Optional[str], dryrun: bool):
        self._phab = None  # type: Optional[Phabricator]
        if not dryrun:
            self._phab = Phabricator(token=token, host=host)
            self._phab.update_interfaces()
    
    @property
    def dryrun(self):
        return self._phab is None

    def _get_revision_id(self, diff: str):
        """Get the revision ID for a diff from Phabricator."""
        if self.dryrun:
            return None

        result = self._phab.differential.querydiffs(ids=[diff])
        return 'D' + result[diff]['revisionID']

    def _comment_on_diff(self, diff: str, text: str):
        """Add a comment to a differential based on the diff_id"""
        print('Sending comment to diff {}:'.format(diff))
        print(text)
        self._comment_on_revision(self._get_revision_id(diff), text)

    def _comment_on_revision(self, revision: str, text: str):
        """Add comment on a differential based on the revision id."""

        transactions = [{
            'type' : 'comment',
            'value' : text
        }]

        if self.dryrun:
            print('differential.revision.edit =================')
            print('Transactions: {}'.format(transactions))
            return
        
        # API details at
        # https://secure.phabricator.com/conduit/method/differential.revision.edit/
        self._phab.differential.revision.edit(objectIdentifier=revision, transactions=transactions)

    def _comment_on_diff_from_file(self, diff: str, text_file_path: str, test_results: TestResults):
        """Comment on a diff, read text from file."""
        header = 'Build result: {} - '.format(test_results.result_type)
        header += '{} tests passed, {} failed and {} were skipped.\n'.format(
            test_results.test_stats['pass'],
            test_results.test_stats['fail'],
            test_results.test_stats['skip'],
        )
        for test_case in test_results.unit:
            if test_case['result'] == 'fail':
                header += '    failed: {}/{}\n'.format(test_case['namespace'], test_case['name'])
        text = ''
        if text_file_path is not None and os.path.exists(text_file_path):           
            with open(text_file_path) as input_file:
                text = input_file.read()
        self._comment_on_diff(diff, header + text)

    def _report_test_results(self, phid: str, test_results: TestResults):
        """Report failed tests to phabricator.

        Only reporting failed tests as the full test suite is too large to upload.
        """

        if self.dryrun:
            print('harbormaster.sendmessage =================')
            print('type: {}'.format(test_results.result_type))
            print('unit: {}'.format(test_results.unit))
            return

        # API details at
        # https://secure.phabricator.com/conduit/method/harbormaster.sendmessage/  
        self._phab.harbormaster.sendmessage(buildTargetPHID=phid, type=test_results.result_type, 
            unit=test_results.unit)

    def _compute_test_results(self, build_result_file: str) -> TestResults:
        result = TestResults()

        if build_result_file is None:
            # If no result file is specified: assume this is intentional
            result.result_type = 'pass'
            return result
        if not os.path.exists(build_result_file):
            print('Warning: Could not find test results file: {}'.format(build_result_file))
            result.result_type = 'pass'
            return result
        
        root_node = etree.parse(build_result_file)
        result.result_type = 'pass'
        
        for test_case in root_node.xpath('//testcase'):
            test_result = self._test_case_status(test_case)
            result.test_stats[test_result] += 1

            if test_result == 'fail':
                failure = test_case.find('failure')
                test_result = {
                    'name' : test_case.attrib['name'],
                    'namespace' : test_case.attrib['classname'],
                    'result' : test_result,
                    'duration' : float(test_case.attrib['time']),
                    'details' : failure.text
                }
                result.result_type = 'fail'
                result.unit.append(test_result)        
        return result

    @staticmethod
    def _test_case_status(test_case) -> str:
        """Get the status of a test case based on an etree node."""
        if test_case.find('failure') is not None:
            return 'fail'
        if test_case.find('skipped') is not None:
            return 'skip'
        return 'pass'

    def report_all(self, diff_id: str, ph_id: str, test_result_file: str, comment_file: str):
        test_results = self._compute_test_results(test_result_file)
        self._report_test_results(ph_id, test_results)
        self._comment_on_diff_from_file(diff_id, comment_file, test_results)
        print('reporting completed.')


def main():
    args = _parse_args()
    errorcount = 0
    while True:
        # retry on connenction problems
        try:
            p = PhabTalk(args.conduit_token, args.host, args.dryrun)
            p.report_all(args.diff_id, args.ph_id, args.test_result_file, args.comment_file)
        except socket.timeout as e:
            errorcount += 1
            if errorcount > 5:
                print('Connection to Pharicator failed, giving up: {}'.format(e))
                raise
            print('Connection to Pharicator failed, retrying: {}'.format(e))
            time.sleep(errorcount*10)
        break


def _parse_args():
    parser = argparse.ArgumentParser(description='Write build status back to Phabricator.')
    parser.add_argument('ph_id', type=str)
    parser.add_argument('diff_id', type=str)   
    parser.add_argument('--comment-file', type=str, dest='comment_file', default=None)
    parser.add_argument('--test-result-file', type=str, dest='test_result_file',
        default=os.path.join(os.path.curdir,'test-results.xml'))
    parser.add_argument('--conduit-token', type=str, dest='conduit_token', default=None)
    parser.add_argument('--host', type=str, dest='host', default="None", 
        help="full URL to API with trailing slash, e.g. https://reviews.llvm.org/api/")
    parser.add_argument('--dryrun', action='store_true',help="output results to the console, do not report back to the server")
    
    return parser.parse_args()    


if __name__ == '__main__':
    main()