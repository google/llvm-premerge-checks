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
import requests

def main(review_number, api_key):
    buildkite = requests.Session()
    buildkite.headers.update({'Authorization': 'Bearer {}'.format(api_key)})
    api = lambda query: 'https://api.buildkite.com/v2' + query

    builds = buildkite.get(api('/organizations/llvm-project/builds?state[]=scheduled&state[]=running')).json()
    for build in builds:
        if build['message'] == review_number:
            pipeline = build['pipeline']['slug']
            buildkite.put(api('/organizations/llvm-project/pipelines/{}/builds/{}/cancel'.format(pipeline, build['number'])))

if __name__ == '__main__':
    review_number = 'D{}'.format(os.getenv('ph_buildable_revision'))
    api_key = # TODO where do we get that? The agents on the service queue need to have the proper access (read_builds and write_builds)
    main(review_number, api_key)
