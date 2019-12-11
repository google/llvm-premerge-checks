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
import re
import socket
import time
from typing import Optional

from lxml import etree
from phabricator import Phabricator


class TestResults:

    def __init__(self):
        self.result_type = None  # type: str
        self.unit = []  #type: List
        self.lint = []
        self.test_stats = {
            'pass':0,
            'fail':0, 
            'skip':0
        }  # type: Dict[str, int]


class PhabTalk:
    """Talk to Phabricator to upload build results.
       See https://secure.phabricator.com/conduit/method/harbormaster.sendmessage/
    """

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

    def _comment_on_diff_from_file(self, diff: str, text_file_path: str, test_results: TestResults, buildresult:str):
        """Comment on a diff, read text from file."""
        header = ''
        if test_results.result_type is None:
            # do this if there are no test results
            header = 'Build result: {} - '.format(buildresult)
        else:
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
        
        if len(header+text) == 0:
            print('Comment for Phabricator would be empty. Not posting it.')
            return
        
        self._comment_on_diff(diff, header + text)

    def _report_test_results(self, phid: str, test_results: TestResults, build_result: str):
        """Report failed tests to phabricator.

        Only reporting failed tests as the full test suite is too large to upload.
        """

        # use jenkins build status if possible
        result = self._translate_jenkins_status(build_result)
        # fall back to test results if Jenkins status is not availble
        if result is None:
            result = test_results.result_type
        # If we do not have a proper status: fail the build.
        if result is None:
            result = 'fail'

        if self.dryrun:
            print('harbormaster.sendmessage =================')
            print('type: {}'.format(result))
            print('unit: {}'.format(test_results.unit))
            print('lint: {}'.format(test_results.lint))
            return

        # API details at
        # https://secure.phabricator.com/conduit/method/harbormaster.sendmessage/  
        self._phab.harbormaster.sendmessage(
            buildTargetPHID=phid,
            type=result, 
            unit=test_results.unit,
            lint=test_results.lint)

    def _compute_test_results(self, build_result_file: str, clang_format_patch: str) -> TestResults:
        result = TestResults()

        if build_result_file is None:
            # If no result file is specified: assume this is intentional
            result.result_type = None
            return result
        if not os.path.exists(build_result_file):
            print('Warning: Could not find test results file: {}'.format(build_result_file))
            result.result_type = None
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
        if os.path.exists(clang_format_patch):
            diffs = self.parse_patch(open(clang_format_patch, 'rt'))
            for d in diffs:
                lint_message = {
                    'name': 'Please fix the formatting',
                    'severity': 'autofix',
                    'code': 'clang-format',
                    'path': d['filename'],
                    'line': d['line'],
                    'char': 1,
                    'description': '```\n' + d['diff'] + '\n```',
                }
                result.lint.append(lint_message)
        return result

    def parse_patch(self, patch) -> []:
        """Extract the changed lines from `patch` file.
        The return value is a list of dictionaries {filename, line, diff}.
        Diff must be generated with -U0 (no context lines).
        """
        entries = []
        lines = []
        filename = None
        line_number = 0
        for line in patch:
            match = re.search(r'^(\+\+\+|---) [^/]+/(.*)', line)
            if match:
                if len(lines) > 0:
                    entries.append({
                        'filename': filename,
                        'diff': ''.join(lines),
                        'line': line_number,
                    })
                    lines = []
                filename = match.group(2).rstrip('\r\n')
                continue
            match = re.search(r'^@@ -(\d+)(,(\d+))? \+(\d+)(,(\d+))?', line)
            if match:
                if len(lines) > 0:
                    entries.append({
                        'filename': filename,
                        'diff': ''.join(lines),
                        'line': line_number,
                    })
                    lines = []
                line_number = int(match.group(1))
                continue
            if line.startswith('+') or line.startswith('-'):
                lines.append(line)
        if len(lines) > 0:
            entries.append({
                'filename': filename,
                'diff': ''.join(lines),
                'line': line_number,
            })
        return entries

    @staticmethod
    def _test_case_status(test_case) -> str:
        """Get the status of a test case based on an etree node."""
        if test_case.find('failure') is not None:
            return 'fail'
        if test_case.find('skipped') is not None:
            return 'skip'
        return 'pass'

    def report_all(self, diff_id: str, ph_id: str, test_result_file: str,
        comment_file: str, build_result: str, clang_format_patch: str):
        test_results = self._compute_test_results(test_result_file, clang_format_patch)

        self._report_test_results(ph_id, test_results, build_result)
        self._comment_on_diff_from_file(diff_id, comment_file, test_results, build_result)
        print('reporting completed.')

    @staticmethod
    def _translate_jenkins_status(jenkins_status: str) -> str:
        """
        Translate the build status form Jenkins to Phabricator.

        Jenkins semantics: https://jenkins.llvm-merge-guard.org/pipeline-syntax/globals#currentBuild
        Phabricator semantics: https://reviews.llvm.org/conduit/method/harbormaster.sendmessage/
        """
        if jenkins_status.lower() == 'success':
            return 'pass'
        if jenkins_status.lower() == 'null':
            return 'working'
        return 'fail'

def main():
    args = _parse_args()
    errorcount = 0
    while True:
        # retry on connenction problems
        try:
            # TODO: separate build of test results and sending the individual messages (to diff and test results)
            p = PhabTalk(args.conduit_token, args.host, args.dryrun)
            p.report_all(args.diff_id, args.ph_id, args.test_result_file,
                         args.comment_file, args.buildresult,
                         args.clang_format_patch)
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
    parser.add_argument('--buildresult', type=str, default=None,
                        choices=['SUCCESS', 'UNSTABLE', 'FAILURE', 'null'])
    parser.add_argument('--clang-format-patch', type=str, default=None,
                        dest='clang_format_patch',
                        help="patch produced by git-clang-format")
    return parser.parse_args()    


if __name__ == '__main__':
    main()