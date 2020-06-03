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
import sys
import uuid

if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# from phabtalk import PhabTalk
# else:
from phabtalk.phabtalk import PhabTalk


def maybe_add_url_artifact(phab: PhabTalk, phid: str, url: str, name: str):
    if phid is None:
        logging.warning('PHID is not provided, cannot create URL artifact')
        return
    phab.create_artifact(phid, str(uuid.uuid4()), 'uri', {'uri': url, 'ui.external': True, 'name': name})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Runs premerge checks8')
    parser.add_argument('--url', type=str)
    parser.add_argument('--name', type=str)
    parser.add_argument('--phid', type=str)
    parser.add_argument('--log-level', type=str, default='WARNING')
    args = parser.parse_args()

    logging.basicConfig(level=args.log_level, format='%(levelname)-7s %(message)s')
    phabtalk = PhabTalk(os.getenv('CONDUIT_TOKEN'), 'https://reviews.llvm.org/api/', False)
    maybe_add_url_artifact(phabtalk, args.phid, args.url, args.name)
