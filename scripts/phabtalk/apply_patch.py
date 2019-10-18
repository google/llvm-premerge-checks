#!/bin/env python3
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
import argparse
import os
import subprocess
from phabricator import Phabricator


def main():
    args = _parse_args()
    diff_id = os.environ['DIFF_ID']
    phid = os.environ['PHID']

    phab = Phabricator(token=args.conduit_token, host=args.host+'/api/')
    phab.update_interfaces()

    _git_checkout(_get_parent_hash(diff_id, phab))
    _apply_patch(diff_id, args.conduit_token, args.host)


def _get_parent_hash(diff_id: str, phab:Phabricator) -> str:
    diff = phab.differential.getdiff(diff_id=diff_id)
    return diff['sourceControlBaseRevision']


def _git_checkout(git_hash:str):
    subprocess.check_call('git reset --hard "{}"'.format(git_hash), shell=True)
    subprocess.check_call('git clean -fdx', shell=True)


def _apply_patch(diff_id: str, conduit_token: str, host: str):
    cmd = 'arc  patch --nobranch --no-ansi --diff "{}" --nocommit '\
            '--conduit-token "{}" --conduit-uri "{}"'.format(
        diff_id, conduit_token, host )
    subprocess.call(cmd, shell=True)


def _parse_args():
    parser = argparse.ArgumentParser(description='Apply a phabricator patch.')
    parser.add_argument('--conduit-token', type=str, dest='conduit_token', default=None)
    parser.add_argument('--host', type=str, dest='host', default="None", 
        help="full URL to API without trailing slash, e.g. https://reviews.llvm.org")
    
    return parser.parse_args()    


if __name__ == "__main__":
    main()

