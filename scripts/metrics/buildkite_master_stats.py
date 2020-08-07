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

# -----------------------------------------------------------------------------
# This script will collect all breakages of the master branch builds from
# buildkite and format the results nicely.
# Arguments:
#     llvm-path :  folder where the LLVM checkout is kept
#     token     :  Access token for buildkite 
# -----------------------------------------------------------------------------

import requests
import git
import argparse
import json 
import os
import datetime

class Build:

  def __init__(self, json_dict):
    self._json_dict = json_dict

  @property
  def number(self) -> int:
    return self._json_dict['number']

  @property
  def web_url(self) -> str:
    return self._json_dict['web_url']

  @property
  def state(self) -> str:
    return self._json_dict['state']

  @property
  def has_passed(self) -> bool:
    return self.state == 'passed'

  @property
  def commit(self) -> str:
    return self._json_dict['commit']

  @property
  def created_at(self) -> datetime.datetime:
    #example: 2019-11-07T14:13:07.942Z
    return datetime.datetime.fromisoformat(self._json_dict['created_at'].rstrip('Z'))


class BuildKiteMasterStats:

  def __init__(self, llvm_repo: str, token_path: str):
    self._llvm_repo = llvm_repo
    with open(token_path, 'r') as token_file:
      self._token = token_file.read().strip()

  def get_stats(self, organisation: str, pipeline: str):
    url = "https://api.buildkite.com/v2/organizations/{}/pipelines/{}/builds".format(organisation, pipeline)
    return self._get_url(url)
    

  def _get_url(self, url: str):
    """Get paginated results from server."""
    page = 1
    results = []
    while True:
      page_url = url + f"?api_key={self._token}&page={page}&per_page=100"
      new_results = requests.get(page_url).json()
      results.extend(new_results)
      print(len(new_results))
      if len(new_results) < 100:
        break
      page += 1 
    return results

  def save_results(self, output_path:str, data):
    with open(output_path, 'w') as output_file:
      json.dump(data, output_file)

  def get_builds(self, json_path: str):
    with open(json_path) as json_file:
      builds = json.load(json_file)
    build_dict = {}
    for b in builds:
      build = Build(b)
      build_dict[build.number] = build
    return build_dict

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Process some integers.')
  parser.add_argument('llvm_path')
  parser.add_argument('token')
  args = parser.parse_args()
  CACHE_FILE = 'tmp/bklogs.json'
  bk = BuildKiteMasterStats(args.llvm_path, args.token)
  
  if not os.path.exists(CACHE_FILE):
    results = bk.get_stats('llvm-project','llvm-master-build')
    bk.save_results(CACHE_FILE, results)
  
  builds = bk.get_builds(CACHE_FILE)
  last_fail = None
  fail_count = 0
  start_time = None
  for build_number in sorted(builds.keys()):
    if build_number < 50:
      # skip the first builds as they might not be mature enough
      continue
    build = builds[build_number]
    if build.has_passed:
      if last_fail is not None:
        print(f'* ends with [build {build.number}]({build.web_url})')
        print(f'* ends with commit {build.commit}')
        print(f'* ends on {build.created_at}')
        duration = build.created_at - start_time
        print(f'* duration: {duration} [h:m:s]')
        print('* cause: # TODO')
        print()
        last_fail = None
    else:
      if last_fail is None:
        print(f'# Outage {fail_count}')
        print()
        print(f'* starts with [build {build.number}]({build.web_url})')
        print(f'* starts with commit {build.commit}')
        print(f'* starts on {build.created_at}')
        fail_count += 1
        start_time = build.created_at
      else:
        pass
      last_fail = build.number
      
  