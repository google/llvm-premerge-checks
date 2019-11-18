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
import json
import os
import subprocess
import sys

from phabricator import Phabricator

def main():
    diff_id = os.environ['DIFF_ID']
    phid = os.environ['PHID']
    conduit_token = os.environ['CONDUIT_TOKEN']
    host = os.environ['PHABRICATOR_HOST']
    diff_json_path = os.environ['DIFF_JSON']
    print('Applying patch for Phabricator diff {} for build {}'.format(diff_id,phid))
    phab = Phabricator(token=conduit_token, host=host+'/api/')
    phab.update_interfaces()

    _git_checkout(_get_parent_hash(diff_id, phab, diff_json_path))
    _apply_patch(diff_id, conduit_token, host)


def _get_parent_hash(diff_id: str, phab: Phabricator, diff_json_path: str) -> str:
    diff = phab.differential.getdiff(diff_id=diff_id)
    # Keep a copy of the Phabricator answer for later usage in a json file
    with open(diff_json_path,'w') as json_file:
        json.dump(diff.response, json_file, sort_keys=True, indent=4)
    return diff['sourceControlBaseRevision']


def _git_checkout(git_hash: str):
    try:
        print('Checking out git hash {}'.format(git_hash))
        subprocess.check_call('git reset --hard {}'.format(git_hash), stdout=sys.stdout, 
            stderr=sys.stderr, shell=True)
    except subprocess.CalledProcessError:
        print('WARNING: checkout of hash failed, using master branch instead.')        
        subprocess.check_call('git checkout master', stdout=sys.stdout, stderr=sys.stderr, 
                              shell=True)
    print('git checkout completed.')


def _apply_patch(diff_id: str, conduit_token: str, host: str):
    print('running arc patch...')
    cmd = 'arc  patch --nobranch --no-ansi --diff "{}" --nocommit '\
            '--conduit-token "{}" --conduit-uri "{}"'.format(
        diff_id, conduit_token, host )
    result = subprocess.run(cmd, capture_output=True, stderr=subprocess.STDOUT, 
                            shell=True, text=True)
    if result.returncode != 0:      
        print('ERROR: arc patch failed with error code {} and message:'.format(result.returncode))
        print(result.stdout + result.stderr)
        raise
    print('Patching completed.')

if __name__ == "__main__":
    main()

