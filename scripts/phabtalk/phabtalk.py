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


class BuildReport:

    def __init__(self):
        self.comments = []
        self.success = True
        self.working = False
        self.unit = []  # type: List
        self.lint = []
        self.test_stats = {
            'pass': 0,
            'fail': 0,
            'skip': 0
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

    def _comment_on_diff(self, diff_id: str, text: str):
        """Add a comment to a differential based on the diff_id"""
        print('Sending comment to diff {}:'.format(diff_id))
        print(text)
        self._comment_on_revision(self._get_revision_id(diff_id), text)

    def _comment_on_revision(self, revision: str, text: str):
        """Add comment on a differential based on the revision id."""

        transactions = [{
            'type': 'comment',
            'value': text
        }]

        if self.dryrun:
            print('differential.revision.edit =================')
            print('Transactions: {}'.format(transactions))
            return

        # API details at
        # https://secure.phabricator.com/conduit/method/differential.revision.edit/
        self._phab.differential.revision.edit(objectIdentifier=revision,
                                              transactions=transactions)

    def submit_report(self, diff_id: str, phid: str, report: BuildReport, build_result: str):
        """Submit collected report to Phabricator.
        """

        result_type = 'pass'
        if report.working:
            result_type = 'working'
        elif not report.success:
            result_type = 'fail'

        if self.dryrun:
            print('harbormaster.sendmessage =================')
            print('type: {}'.format(result_type))
            print('unit: {}'.format(report.unit))
            print('lint: {}'.format(report.lint))
        else:
            _try_call(lambda: self._phab.harbormaster.sendmessage(
                buildTargetPHID=phid,
                type=result_type,
                unit=report.unit,
                lint=report.lint))

        if len(report.comments) > 0:
            _try_call(lambda: self._comment_on_diff(diff_id, '\n\n'.join(report.comments)))


def _parse_patch(patch) -> []:
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


def _add_clang_format(report: BuildReport, clang_format_patch: str, results_dir: str,
                      results_url: str):
    """Populates results from diff produced by clang format."""
    if clang_format_patch is None:
        return
    p = os.path.join(results_dir, clang_format_patch)
    ok = True
    if os.path.exists(p):
        ok = False
        diffs = _parse_patch(open(p, 'rt'))
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
            report.lint.append(lint_message)
    comment = section_title('clang-format', ok)
    if not ok:
        comment += 'Please format your changes with clang-format by running `git-clang-format HEAD^` or apply ' \
                   'this [[ {}/{} | patch ]].'.format(results_url, clang_format_patch)
    report.comments.append(comment)


def _try_call(call):
    """Tries to call function several times retrying on socked.timeout."""
    c = 0
    while True:
        try:
            call()
        except socket.timeout as e:
            c += 1
            if c > 5:
                print('Connection to Pharicator failed, giving up: {}'.format(e))
                raise
            print('Connection to Pharicator failed, retrying: {}'.format(e))
            time.sleep(c * 10)
        break


def _add_test_results(report: BuildReport, build_result_file: str):
    """Populates results from build test results XML.

     Only reporting failed tests as the full test suite is too large to upload.
     """
    if build_result_file is None:
        return
    if not os.path.exists(build_result_file):
        print('Warning: Could not find test results file: {}'.format(
            build_result_file))
        return

    root_node = etree.parse(build_result_file)

    ok = True
    for test_case in root_node.xpath('//testcase'):
        test_result = _test_case_status(test_case)
        report.test_stats[test_result] += 1

        if test_result == 'fail':
            ok = False
            failure = test_case.find('failure')
            test_result = {
                'name': test_case.attrib['name'],
                'namespace': test_case.attrib['classname'],
                'result': test_result,
                'duration': float(test_case.attrib['time']),
                'details': failure.text
            }
            report.unit.append(test_result)

    report.success = ok and report.success
    comment = section_title('Unit tests', ok)
    comment += '{} tests passed, {} failed and {} were skipped.\n'.format(
        report.test_stats['pass'],
        report.test_stats['fail'],
        report.test_stats['skip'],
    )
    for test_case in report.unit:
        if test_case['result'] == 'fail':
            comment += '    failed: {}/{}\n'.format(test_case['namespace'], test_case['name'])
    report.comments.append(comment)


def _add_links_to_artifacts(report: BuildReport, results_dir: str, results_url: str):
    """Comment on a diff, read text from file."""
    file_links = []
    for f in os.listdir(results_dir):
        if not os.path.isfile(os.path.join(results_dir, f)):
            continue
        file_links.append('[[{0}/{1} | {1}]]'.format(results_url, f))
    if len(file_links) > 0:
        report.comments.append('[[ {} | Build artifacts ]]: '.format(results_url) + ', '.join(file_links))


def _test_case_status(test_case) -> str:
    """Get the status of a test case based on an etree node."""
    if test_case.find('failure') is not None:
        return 'fail'
    if test_case.find('skipped') is not None:
        return 'skip'
    return 'pass'


def section_title(title: str, ok: bool) -> str:
    return '{} {}: {}. '.format(
        '{icon check-circle color=green}' if ok else '{icon times-circle color=red}',
        title,
        'pass' if ok else 'fail')


def main():
    args = _parse_args()
    report = BuildReport()

    if args.buildresult is not None:
        print('Jenkins result: {}'.format(args.buildresult))
        if args.buildresult.lower() == 'success':
            pass
        elif args.buildresult.lower() == 'null':
            report.working = True
        else:
            report.success = False

    _add_test_results(report, os.path.join(args.results_dir, args.test_result_file))
    _add_clang_format(report, args.clang_format_patch, args.results_dir, args.results_url)
    _add_links_to_artifacts(report, args.results_dir, args.results_url)
    p = PhabTalk(args.conduit_token, args.host, args.dryrun)
    p.submit_report(args.diff_id, args.ph_id, report, args.buildresult)


def _parse_args():
    parser = argparse.ArgumentParser(
        description='Write build status back to Phabricator.')
    parser.add_argument('ph_id', type=str)
    parser.add_argument('diff_id', type=str)
    parser.add_argument('--test-result-file', type=str, dest='test_result_file',
                        default='test-results.xml')
    parser.add_argument('--conduit-token', type=str, dest='conduit_token',
                        default=None)
    parser.add_argument('--host', type=str, dest='host', default="None",
                        help="full URL to API with trailing slash, e.g. https://reviews.llvm.org/api/")
    parser.add_argument('--dryrun', action='store_true',
                        help="output results to the console, do not report back to the server")
    parser.add_argument('--buildresult', type=str, default=None,
                        choices=['SUCCESS', 'UNSTABLE', 'FAILURE', 'null'])
    parser.add_argument('--clang-format-patch', type=str, default=None,
                        dest='clang_format_patch',
                        help="path to diff produced by git-clang-format, relative to results-dir")
    parser.add_argument('--results-dir', type=str, default=None,
                        dest='results_dir',
                        help="directory of all build artifacts")
    parser.add_argument('--results-url', type=str, default=None,
                        dest='results_url',
                        help="public URL to access results directory")
    return parser.parse_args()


if __name__ == '__main__':
    main()
