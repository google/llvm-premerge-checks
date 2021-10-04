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

import os
import sys

import yaml
import logging
from buildkite_utils import set_metadata, BuildkiteApi
from phabtalk.phabtalk import PhabTalk

if __name__ == '__main__':
    diff_id = os.getenv("ph_buildable_diff")
    revision_id = os.getenv("ph_buildable_revision", '')
    log_level = os.getenv('ph_log_level', 'INFO')
    base_commit = os.getenv('ph_base_commit', 'auto')
    run_build = os.getenv('ph_skip_build') is None
    trigger = os.getenv('ph_trigger_pipeline')
    logging.basicConfig(level=log_level, format='%(levelname)-7s %(message)s')

    phabtalk = PhabTalk(os.getenv('CONDUIT_TOKEN'), dry_run_updates=(os.getenv('ph_dry_run_report') is not None))
    rev = phabtalk.get_revision(int(revision_id))
    user_id = rev.get('authorPHID')
    logging.debug(f'authorPHID {user_id}')
    if user_id is None:
        logging.error('cannot find author of the revision')
        sys.exit(1)
    projects = phabtalk.user_projects(user_id)
    logging.info(f'user projects: {", ".join(projects)}')
    # Cancel any existing builds.
    # Do this before setting own 'ph_buildable_revision'.
    try:
        bk = BuildkiteApi(os.getenv("BUILDKITE_API_TOKEN"), os.getenv("BUILDKITE_ORGANIZATION_SLUG"))
        for b in bk.list_running_revision_builds(os.getenv("BUILDKITE_PIPELINE_SLUG"), os.getenv('ph_buildable_revision')):
            logging.info(f'cancelling build {b.get("web_url")}')
            bk.cancel_build(b)
    except Exception as e:
        logging.error(e)

    set_metadata('ph_buildable_diff', os.getenv("ph_buildable_diff"))
    set_metadata('ph_buildable_revision', os.getenv('ph_buildable_revision'))
    set_metadata('ph_build_id', os.getenv("ph_build_id"))
    if trigger is None:
        trigger = 'premerge-checks'

    env = {
        'ph_scripts_refspec': '${BUILDKITE_BRANCH}',
        'ph_user_project_slugs': ",".join(projects),
        # TODO: those two are for "apply_patch.sh". Maybe just look for "ph_" env in patch_diff.py?
        'LOG_LEVEL': log_level,
        'BASE_COMMIT': base_commit,
    }
    for e in os.environ:
        if e.startswith('ph_'):
            env[e] = os.getenv(e)
    steps = [{
        'label': 'create branch',
        'key': 'create-branch',
        'commands': [
            'pip install -q -r scripts/requirements.txt',
            'scripts/apply_patch.sh'
        ],
        'agents': {'queue': 'service'},
        'timeout_in_minutes': 20,
        'env': env
    }]
    if run_build:
        trigger_build_step = {
            'trigger': trigger,
            'label': ':rocket: build and test',
            'async': False,
            'depends_on': 'create-branch',
            'build': {
                'branch': f'phab-diff-{diff_id}',
                'env': env,
            },
        }
        steps.append(trigger_build_step)
    print(yaml.dump({'steps': steps}))
