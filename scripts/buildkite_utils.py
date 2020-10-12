import logging
import os
import re
import subprocess
from typing import Optional

import backoff
import requests


def upload_file(base_dir: str, file: str):
    """
    Uploads artifact to buildkite and returns URL to it
    """
    r = subprocess.run(f'buildkite-agent artifact upload "{file}"', shell=True, capture_output=True, cwd=base_dir)
    logging.debug(f'upload-artifact {r}')
    match = re.search('Uploading artifact ([^ ]*) ', r.stderr.decode())
    logging.debug(f'match {match}')
    if match:
        url = f'https://buildkite.com/organizations/llvm-project/pipelines/premerge-checks/builds/{os.getenv("BUILDKITE_BUILD_NUMBER")}/jobs/{os.getenv("BUILDKITE_JOB_ID")}/artifacts/{match.group(1)}'
        logging.info(f'uploaded {file} to {url}')
        return url
    else:
        logging.warning(f'could not find artifact {base_dir}/{file}')
        return None


class BuildkiteApi:
    def __init__(self, token: str, organization: str):
        self.token = token
        self.organization = organization

    @backoff.on_exception(backoff.expo, Exception, max_tries=3, logger='', factor=3)
    def get_build(self, pipeline: str, build_number: str):
        authorization = f'Bearer {self.token}'
        # https://buildkite.com/docs/apis/rest-api/builds#get-a-build
        url = f'https://api.buildkite.com/v2/organizations/{self.organization}/pipelines/{pipeline}/builds/{build_number}'
        response = requests.get(url, headers={'Authorization': authorization})
        if response.status_code != 200:
            raise Exception(f'Builkite responded with non-OK status: {re.status_code}')
        return response.json()


def format_url(url: str, name: Optional[str] = None):
    if name is None:
        name = url
    return f"\033]1339;url='{url}';content='{name}'\a\n"
