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
from typing import Optional
from phabricator import Phabricator
from lxml import etree

class PhabTalk:
    """Talk to Phabricator to upload build results."""

    def __init__(self, token: Optional[str], host: Optional[str]):
        self._phab = Phabricator(token=token, host=host)
        self._phab.update_interfaces()

    def get_revision_id(self, diff: str):
        """Get the revision ID for a diff from Phabricator."""
        result = self._phab.differential.querydiffs(ids=[diff])
        return 'D' + result[diff]['revisionID']

    def comment_on_diff(self, diff: str, text: str):
        """Add a comment to a differential based on the diff_id"""
        self.comment_on_revision(self.get_revision_id(diff), text)

    def comment_on_revision(self, revision: str, text: str):
        """Add comment on a differential based on the revision id."""

        transactions = [{
            'type' : 'comment',
            'value' : text
        }]

        # API details at
        # https://secure.phabricator.com/conduit/method/differential.revision.edit/
        self._phab.differential.revision.edit(objectIdentifier=revision, transactions=transactions)

    def comment_on_diff_from_file(self, diff: str, text_file_path: str):
        """Comment on a diff, read text from file."""
        if text_file_path is None:
            return
        if not os.path.exists(text_file_path):
            raise FileNotFoundError('Could not find file with comments: {}'.format(text_file_path))
        
        with open(text_file_path) as input_file:
            text = input_file.read()
        self.comment_on_diff(diff, text)

    def report_test_results(self, phid: str, build_result_file: str):
        """Report failed tests to phabricator.

        Only reporting failed tests as the full test suite is too large to upload.
        """
        if build_result_file is None:
            return
        if not os.path.exists(build_result_file):
            raise FileNotFoundError('Could not find file with build results: {}'.format(build_result_file))
        
        root_node = etree.parse(build_result_file)
        unit_test_results = []
        build_result_type = 'pass'
        for test_case in root_node.xpath('//testcase'):
            test_result = self._test_case_status(test_case)
            if test_result == 'fail':
                failure = test_case.find('failure')
                test_result = {
                    'name' : test_case.attrib['name'],
                    'namespace' : test_case.attrib['classname'],
                    'result' : test_result,
                    'duration' : float(test_case.attrib['time']),
                    'details' : failure.text
                }
                build_result_type = 'fail'
                unit_test_results.append(test_result)

        # API details at
        # https://secure.phabricator.com/conduit/method/harbormaster.sendmessage/  
        self._phab.harbormaster.sendmessage(buildTargetPHID=phid, type=build_result_type, 
            unit=unit_test_results)

    @staticmethod
    def _test_case_status(test_case) -> str:
        """Get the status of a test case based on an etree node."""
        if test_case.find('failure') is not None:
            return 'fail'
        if test_case.find('skipped') is not None:
            return 'skip'
        return 'pass'

def main():
    parser = argparse.ArgumentParser(description='Write build status back to Phabricator.')
    parser.add_argument('ph_id', type=str)
    parser.add_argument('diff_id', type=str)   
    parser.add_argument('--comment-file', type=str, dest='comment_file', default=None)
    parser.add_argument('--test-result-file', type=str, dest='test_result_file',
        default=os.path.join(os.path.curdir,'test-results.xml'))
    parser.add_argument('--conduit-token', type=str, dest='conduit_token', default=None)
    parser.add_argument('--host', type=str, dest='host', default="None", 
        help="full URL to API with trailing slash, e.g. https://reviews.llvm.org/api/")
    args = parser.parse_args()    

    p = PhabTalk(args.conduit_token, args.host)
    p.comment_on_diff_from_file(args.diff_id, args.comment_file)
    p.report_test_results(args.ph_id, args.test_result_file)

if __name__ == '__main__':
    main()