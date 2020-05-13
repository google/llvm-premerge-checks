#!/usr/bin/env bash
scripts/phabtalk/apply_patch2.py $ph_buildable_diff \
  --token $CONDUIT_TOKEN \
  --url $PHABRICATOR_HOST \
  --comment-file apply_patch.txt \
  --push-branch