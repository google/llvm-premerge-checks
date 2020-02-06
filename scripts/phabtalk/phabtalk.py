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
import urllib
import uuid
from typing import Optional, List, Dict

import pathspec
from lxml import etree
from phabricator import Phabricator


class BuildReport:

    def __init__(self):
        self.comments = []
        self.success = True
        self.working = False
        self.unit = []  # type: List
        self.lint = {}
        self.test_stats = {
            'pass': 0,
            'fail': 0,
            'skip': 0
        }  # type: Dict[str, int]

    def addLint(self, m):
        key = '{}:{}'.format(m['path'], m['line'])
        if key not in self.lint:
            self.lint[key] = []
        self.lint[key].append(m)


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

    def get_revision_id(self, diff: str) -> Optional[str]:
        """Get the revision ID for a diff from Phabricator."""
        if self.dryrun:
            return None

        result = self._phab.differential.querydiffs(ids=[diff])
        return 'D' + result[diff]['revisionID']

    def _comment_on_diff(self, diff_id: str, text: str):
        """Add a comment to a differential based on the diff_id"""
        print('Sending comment to diff {}:'.format(diff_id))
        print(text)
        revision_id = self.get_revision_id(diff_id)
        if revision_id is not None:
            self._comment_on_revision(revision_id, text)

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

        # Group lint messages by file and line.
        lint_messages = []
        for v in report.lint.values():
            path = ''
            line = 0
            descriptions = []
            for e in v:
                path = e['path']
                line = e['line']
                descriptions.append('{}: {}'.format(e['name'], e['description']))
            lint_message = {
                'name': 'Pre-merge checks',
                'severity': 'warning',
                'code': 'llvm-premerge-checks',
                'path': path,
                'line': line,
                'description': '\n'.join(descriptions),
            }
            lint_messages.append(lint_message)

        if self.dryrun:
            print('harbormaster.sendmessage =================')
            print('type: {}'.format(result_type))
            print('unit: {}'.format(report.unit))
            print('lint: {}'.format(lint_messages))
        else:
            _try_call(lambda: self._phab.harbormaster.sendmessage(
                buildTargetPHID=phid,
                type=result_type,
                unit=report.unit,
                lint=lint_messages))

        if len(report.comments) > 0:
            _try_call(lambda: self._comment_on_diff(diff_id, '\n\n'.join(report.comments)))

    def add_artifact(self, phid: str, file: str, name: str, results_url: str):
        _try_call(lambda: self._phab.harbormaster.createartifact(
            buildTargetPHID=phid,
            artifactKey=str(uuid.uuid4()),
            artifactType='uri',
            artifactData={'uri': '{}/{}'.format(results_url, file),
                          'ui.external': True,
                          'name': name}))


def _parse_patch(patch) -> List[Dict[str,str]]:
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


def _add_clang_format(report: BuildReport, results_dir: str,
                      results_url: str, clang_format_patch: str, pt: PhabTalk, ph_id: str):
    """Populates results from diff produced by clang format."""
    present = (clang_format_patch is not None) and os.path.exists(os.path.join(results_dir, clang_format_patch))
    if not present:
        print('clang-format result {} is not found'.format(clang_format_patch))
        report.comments.append(section_title('clang-format', False, False))
        return
    p = os.path.join(results_dir, clang_format_patch)
    if os.stat(p).st_size != 0:
        pt.add_artifact(ph_id, clang_format_patch, "clang-format", results_url)
    diffs = _parse_patch(open(p, 'r'))
    success = len(diffs) == 0
    for d in diffs:
        report.addLint({
            'name': 'clang-format',
            'severity': 'autofix',
            'code': 'clang-format',
            'path': d['filename'],
            'line': d['line'],
            'char': 1,
            'description': 'please reformat the code\n```\n' + d['diff'] + '\n```',
        })
    comment = section_title('clang-format', success, present)
    if not success:
        comment += 'Please format your changes with clang-format by running `git-clang-format HEAD^` or applying ' \
                   'this [[ {}/{} | patch ]].'.format(results_url, clang_format_patch)
    report.comments.append(comment)
    report.success = success and report.success


def _add_clang_tidy(report: BuildReport, results_dir: str, results_url: str, workspace: str, clang_tidy_file: str,
                    clang_tidy_ignore: str, pt: PhabTalk, ph_id: str):
    # Typical message looks like
    # [..]/clang/include/clang/AST/DeclCXX.h:3058:20: error: no member named 'LifetimeExtendedTemporary' in 'clang::Decl' [clang-diagnostic-error]
    pattern = '^{}/([^:]*):(\\d+):(\\d+): (.*): (.*)'.format(workspace)
    errors_count = 0
    warn_count = 0
    inline_comments = 0
    present = (clang_tidy_file is not None) and os.path.exists(os.path.join(results_dir, clang_tidy_file))
    if not present:
        print('clang-tidy result {} is not found'.format(clang_tidy_file))
        report.comments.append(section_title('clang-tidy', False, False))
        return
    present = (clang_tidy_ignore is not None) and os.path.exists(clang_tidy_ignore)
    if not present:
        print('clang-tidy ignore file {} is not found'.format(clang_tidy_ignore))
        report.comments.append(section_title('clang-tidy', False, False))
        return
    p = os.path.join(results_dir, clang_tidy_file)
    if os.stat(p).st_size != 0:
        pt.add_artifact(ph_id, clang_tidy_file, "clang-tidy", results_url)
    ignore = pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern,
                                          open(clang_tidy_ignore, 'r').readlines())
    for line in open(p, 'r'):
        match = re.search(pattern, line)
        if match:
            file_name = match.group(1)
            line_pos = match.group(2)
            char_pos = match.group(3)
            severity = match.group(4)
            text = match.group(5)
            text += '\n[[https://github.com/google/llvm-premerge-checks/blob/master/docs/clang_tidy.md#warning-is-not' \
                    '-useful | not useful]] '
            if severity in ['warning', 'error']:
                if severity == 'warning':
                    warn_count += 1
                if severity == 'error':
                    errors_count += 1
                if ignore.match_file(file_name):
                    print('{} is ignored by pattern and no comment will be added'.format(file_name))
                else:
                    inline_comments += 1
                    report.addLint({
                        'name': 'clang-tidy',
                        'severity': 'warning',
                        'code': 'clang-tidy',
                        'path': file_name,
                        'line': int(line_pos),
                        'char': int(char_pos),
                        'description': '{}: {}'.format(severity, text),
                    })
    success = errors_count + warn_count == 0
    comment = section_title('clang-tidy', success, present)
    if not success:
        comment += "clang-tidy found [[ {}/{} | {} errors and {} warnings]]. {} of them are added as review comments " \
                   "below ([[https://github.com/google/llvm-premerge-checks/blob/master/docs/clang_tidy.md#review" \
                   "-comments | why?]])." \
            .format(results_url, clang_tidy_file, errors_count, warn_count, inline_comments)

    report.comments.append(comment)
    report.success = success and report.success


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


def _add_test_results(report: BuildReport, results_dir: str, build_result_file: str):
    """Populates results from build test results XML.

     Only reporting failed tests as the full test suite is too large to upload.
     """

    success = True
    present = (build_result_file is not None) and os.path.exists(os.path.join(results_dir, build_result_file))
    if not present:
        print('Warning: Could not find test results file: {}'.format(build_result_file))
        report.comments.append(section_title('Unit tests', False, present))
        return

    root_node = etree.parse(os.path.join(results_dir, build_result_file))
    for test_case in root_node.xpath('//testcase'):
        test_result = _test_case_status(test_case)
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

    comment = section_title('Unit tests', success, True)
    comment += '{} tests passed, {} failed and {} were skipped.\n'.format(
        report.test_stats['pass'],
        report.test_stats['fail'],
        report.test_stats['skip'],
    )
    for test_case in report.unit:
        if test_case['result'] == 'fail':
            comment += '    failed: {}/{}\n'.format(test_case['namespace'], test_case['name'])
    report.comments.append(comment)
    report.success = success and report.success


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


def section_title(title: str, ok: bool, present: bool) -> str:
    icon = '{icon question-circle color=gray}'
    result = 'unknown'
    if present:
        icon = '{icon check-circle color=green}' if ok else '{icon times-circle color=red}'
        result = 'pass' if ok else 'fail'
    return '{} {}: {}. '.format(icon, title, result)


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

    p = PhabTalk(args.conduit_token, args.host, args.dryrun)
    _add_test_results(report, args.results_dir, args.test_result_file)
    _add_clang_tidy(report, args.results_dir, args.results_url, args.workspace, args.clang_tidy_result,
                    args.clang_tidy_ignore, p, args.ph_id)
    _add_clang_format(report, args.results_dir, args.results_url, args.clang_format_patch, p, args.ph_id)
    _add_links_to_artifacts(report, args.results_dir, args.results_url)

    with open(os.path.join(args.results_dir, 'summary.html'), 'w') as f:
        f.write('<html><body>Build summary:<br/><a href="clang-tidy.txt">clang-tidy</a></body></html>')
    p.add_artifact(args.ph_id, 'summary.html', 'summary', args.results_url)

    title = 'Issue with build for {} ({})'.format(p.get_revision_id(args.diff_id), args.diff_id)
    report.comments.append(
        '//Pre-merge checks is in beta. [[ https://github.com/google/llvm-premerge-checks/issues/new?assignees'
        '=&labels=bug&template=bug_report.md&title={} | Report issue]]. '
        'Please [[ https://reviews.llvm.org/project/update/78/join/ | join beta ]] or '
        '[[ https://github.com/google/llvm-premerge-checks/issues/new?assignees=&labels=enhancement&template'
        '=&title=enable%20checks%20for%20{{PATH}} | enable it for your project ]].//'.format(
            urllib.parse.quote(title)))
    p.submit_report(args.diff_id, args.ph_id, report, args.buildresult)


def _parse_args():
    parser = argparse.ArgumentParser(
        description='Write build status back to Phabricator.')
    parser.add_argument('ph_id', type=str)
    parser.add_argument('diff_id', type=str)
    parser.add_argument('--test-result-file', type=str, dest='test_result_file', default='test-results.xml')
    parser.add_argument('--conduit-token', type=str, dest='conduit_token', required=True)
    parser.add_argument('--host', type=str, dest='host', default="https://reviews.llvm.org/api/",
                        help="full URL to API with trailing slash, e.g. https://reviews.llvm.org/api/")
    parser.add_argument('--dryrun', action='store_true',
                        help="output results to the console, do not report back to the server")
    parser.add_argument('--buildresult', type=str, default=None, choices=['SUCCESS', 'UNSTABLE', 'FAILURE', 'null'])
    parser.add_argument('--clang-format-patch', type=str, default=None,
                        dest='clang_format_patch',
                        help="path to diff produced by git-clang-format, relative to results-dir")
    parser.add_argument('--clang-tidy-result', type=str, default=None,
                        dest='clang_tidy_result',
                        help="path to diff produced by git-clang-tidy, relative to results-dir")
    parser.add_argument('--clang-tidy-ignore', type=str, default=None,
                        dest='clang_tidy_ignore',
                        help="path to file with patters to exclude commenting on for clang-tidy findings")
    parser.add_argument('--results-dir', type=str, default=None, required=True,
                        dest='results_dir',
                        help="directory of all build artifacts")
    parser.add_argument('--results-url', type=str, default=None,
                        dest='results_url',
                        help="public URL to access results directory")
    parser.add_argument('--workspace', type=str, required=True, help="path to workspace")
    return parser.parse_args()


if __name__ == '__main__':
    main()
