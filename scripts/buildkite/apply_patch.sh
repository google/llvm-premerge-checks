#!/usr/bin/env bash
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

# Scripts that use secrets has to be a separate files, not inlined in pipeline:
# https://buildkite.com/docs/pipelines/secrets#anti-pattern-referencing-secrets-in-your-pipeline-yaml

set -uo pipefail

scripts/phabtalk/apply_patch2.py $ph_buildable_diff \
  --path "${BUILDKITE_BUILD_PATH}"/llvm-project-fork \
  --token $CONDUIT_TOKEN \
  --url $PHABRICATOR_HOST \
  --comment-file apply_patch.txt \
  --push-branch

EXIT_STATUS=$?

if [ $EXIT_STATUS -ne 0 ]; then
  scripts/phabtalk/add_url_artifact.py --phid="$ph_target_phid" --url="$BUILDKITE_BUILD_URL" --name="Buildkite apply patch"
  scripts/buildkite/set_build_status.py
  echo failed
fi

exit $EXIT_STATUS