import logging
import os
import re
import subprocess
import urllib.parse
import shlex
from typing import Optional

import backoff
import requests

context_style = {}
styles = ['default', 'info', 'success', 'warning', 'error']


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


def annotate(message: str, style: str = 'default', context: str = 'default', append: bool = True):
    """
    Adds an annotation for that currently running build.
    Note that last `style` applied to the same `context` takes precedence.
    """
    if style not in styles:
        style = 'default'
    # Pick most severe style so far.
    context_style.setdefault(context, 0)
    context_style[context] = max(styles.index(style), context_style[context])
    style = styles[context_style[context]]
    if append:
        message += '\n\n'
    r = subprocess.run(f"buildkite-agent annotate {shlex.quote(message)}"
                       f' --style={shlex.quote(style)}'
                       f" {'--append' if append else ''}"
                       f" --context={shlex.quote(context)}", shell=True, capture_output=True)
    logging.debug(f'annotate call {r}')
    if r.returncode != 0:
        logging.warning(message)


def feedback_url():
    title = f"buildkite build {os.getenv('BUILDKITE_PIPELINE_SLUG')} {os.getenv('BUILDKITE_BUILD_NUMBER')}"
    return f'https://github.com/google/llvm-premerge-checks/issues/new?assignees=&labels=bug' \
           f'&template=bug_report.md&title={urllib.parse.quote(title)}'


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
            raise Exception(f'Builkite responded with non-OK status: {response.status_code}')
        return response.json()


def format_url(url: str, name: Optional[str] = None):
    if name is None:
        name = url
    return f"\033]1339;url='{url}';content='{name}'\a\n"
