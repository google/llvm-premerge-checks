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

import csv
import datetime
import gzip
import os
import mailbox
import requests
import re
from typing import List, Dict, Set


EMAIL_ARCHIVE_URL = 'http://lists.llvm.org/pipermail/llvm-dev/{year}-{month}.txt.gz'
TMP_DIR = os.path.join(os.path.dirname(__file__), 'tmp')


class LLVMBotArchiveScanner:

    def __init__(self):
        self._tmpdir = TMP_DIR

    @staticmethod
    def _generate_archive_url(month: datetime.date) -> str:
        return EMAIL_ARCHIVE_URL.format(year=month.year, month=month.strftime('%B'))

    def _download_archive(self, month: datetime.date):
        os.makedirs(self._tmpdir, exist_ok=True)
        filename = os.path.join(self._tmpdir, 'llvmdev-{year}-{month:02d}.txt'.format(year=month.year, month=month.month))
        url = self._generate_archive_url(month)
        # FIXME: decompress the files
        self.download(url, filename)

    def get_archives(self, start_month: datetime.date):
        print('Downloading data...')
        month = start_month
        today = datetime.date.today()
        while month < today:
            self._download_archive(month)
            if month.month < 12:
                month = datetime.date(year=month.year, month=month.month+1, day=1)
            else:
                month = datetime.date(year=month.year+1, month=1, day=1)

    def extract_emails(self) -> List[mailbox.Message]:
        result = []
        for archive_name in (d for d in os.listdir(self._tmpdir) if d.startswith('llvmdev-')):
            print('Scanning {}'.format(archive_name))
            mb = mailbox.mbox(os.path.join(self._tmpdir, archive_name), factory=mbox_reader)
            for mail in mb.values():
                subject = mail.get('subject')
                if subject is None:
                    continue
                if 'Buildbot numbers' in mail['subject']:
                    yield(mail)
        yield

    def get_attachments(self, email: mailbox.Message):
        if email is None:
            return
        week_str = re.search(r'(\d+/\d+/\d+)', email['subject']).group(1)
        week = datetime.datetime.strptime(week_str, '%m/%d/%Y').date()
        attachment_url = re.search(r'Name: completed_failed_avr_time.csv[^<]*URL: <([^>]+)>', email.get_payload(), re.DOTALL).group(1)
        filename = os.path.join(self._tmpdir, 'buildbot_stats_{}.csv'.format(week.isoformat()))
        self.download(attachment_url, filename)

    @staticmethod
    def download(url, filename):
        if os.path.exists(filename):
            return
        r = requests.get(url)
        print('Getting {}'.format(filename))
        with open(filename, 'wb') as f:
            f.write(r.content)

    def merge_results(self):
        def _convert_int(s: str) -> int:
            if len(s) == 0:
                return 0
            return int(s)

        bot_stats = {}  # type: Dict[str, Dict[datetime.date, float]]
        weeks = set()  # type: Set[datetime.date]
        for csv_filename in (d for d in os.listdir(self._tmpdir) if d.startswith('buildbot_stats_')):
            week_str = re.search(r'(\d+-\d+-\d+)', csv_filename).group(1)
            week = datetime.datetime.fromisoformat(week_str).date()
            weeks.add(week)
            with open(os.path.join(self._tmpdir, csv_filename)) as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    name = row['name']
                    red_build = _convert_int(row['red_builds'])
                    all_builds = _convert_int(row['all_builds'])
                    percentage = 100.0 * red_build / all_builds
                    bot_stats.setdefault(name, {})
                    bot_stats[name][week] = percentage

        with open(os.path.join(self._tmpdir, 'buildbot_weekly.csv'), 'w') as csv_file:
            fieldnames = ['week']
            filtered_bots = sorted(b for b in bot_stats.keys()) # if len(bot_stats[b]) == len(weeks)
            fieldnames.extend(filtered_bots)
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            for week in sorted(weeks):
                row = {'week': week.isoformat()}
                for bot in filtered_bots:
                    percentage = bot_stats[bot].get(week)
                    if percentage is None:
                        continue
                    row[bot] = percentage
                writer.writerow(row)


def mbox_reader(stream):
    """Read a non-ascii message from mailbox.

    Based on https://stackoverflow.com/questions/37890123/how-to-trap-an-exception-that-occurs-in-code-underlying-python-for-loop
    """
    data = stream.read()
    text = data.decode(encoding="utf-8")
    return mailbox.mboxMessage(text)


if __name__ == '__main__':
    scanner = LLVMBotArchiveScanner()
    scanner.get_archives(datetime.date(year=2019, month=8, day=1))
    for message in scanner.extract_emails():
        scanner.get_attachments(message)
    scanner.merge_results()