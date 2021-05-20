#!/usr/bin/env bash
echo "loading buildkite data"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd $SCRIPT_DIR
pipenv install
cloud_sql_proxy -instances=llvm-premerge-checks:us-central1:buildkite-stats=tcp:0.0.0.0:5432 & pipenv run python3 $SCRIPT_DIR/load_buildkite.py
