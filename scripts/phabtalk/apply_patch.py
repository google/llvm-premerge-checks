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
    diff_id = os.environ['DIFF_ID']
    phid = os.environ['PHID']
    conduit_token = os.environ['CONDUIT_TOKEN']
    host = os.environ['PHABRICATOR_HOST']

    phab = Phabricator(token=conduit_token, host=host+'/api/')
    phab.update_interfaces()

    _git_checkout(_get_parent_hash(diff_id, phab))
    _apply_patch(diff_id, conduit_token, host)


def _get_parent_hash(diff_id: str, phab:Phabricator) -> str:
    diff = phab.differential.getdiff(diff_id=diff_id)
    return diff['sourceControlBaseRevision']


def _git_checkout(git_hash:str):
    try:
        subprocess.check_call('git reset --hard {}'.format(git_hash), shell=True)
    except CalledProcessError:
        subprocess.check_call('git checkout master')
    subprocess.check_call('git clean -fdx', shell=True)


def _apply_patch(diff_id: str, conduit_token: str, host: str):
    cmd = 'arc  patch --nobranch --no-ansi --diff "{}" --nocommit '\
            '--conduit-token "{}" --conduit-uri "{}"'.format(
        diff_id, conduit_token, host )
    subprocess.call(cmd, shell=True)

if __name__ == "__main__":
    main()

