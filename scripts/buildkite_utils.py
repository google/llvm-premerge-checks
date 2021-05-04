import logging
import os
import re
import subprocess
import urllib.parse
from typing import Optional
from benedict import benedict

import backoff
import requests

context_style = {}
previous_context = 'default'
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


def set_metadata(key: str, value: str):
    r = subprocess.run(f'buildkite-agent meta-data set "{key}" "{value}"', shell=True, capture_output=True)
    if r.returncode != 0:
        logging.warning(r)


def annotate(message: str, style: str = 'default', context: Optional[str] = None, append: bool = True):
    """
    Adds an annotation for that currently running build.
    Note that last `style` applied to the same `context` takes precedence.
    """
    global previous_context, styles, context_style
    if style not in styles:
        style = 'default'
    if context is None:
        context = previous_context
    previous_context = context
    # Pick most severe style so far.
    context_style.setdefault(context, 0)
    context_style[context] = max(styles.index(style), context_style[context])
    style = styles[context_style[context]]
    if append:
        message += '\n\n'
    cmd = ['buildkite-agent', 'annotate', message, '--style', style, '--context', context]
    if append:
        cmd.append('--append')
    r = subprocess.run(cmd, capture_output=True)
    logging.debug(f'annotate call {r}')
    if r.returncode != 0:
        logging.warning(r)


def feedback_url():
    title = f"buildkite build {os.getenv('BUILDKITE_PIPELINE_SLUG')} {os.getenv('BUILDKITE_BUILD_NUMBER')}"
    return f'https://github.com/google/llvm-premerge-checks/issues/new?assignees=&labels=bug' \
           f'&template=bug_report.md&title={urllib.parse.quote(title)}'


class BuildkiteApi:
    def __init__(self, token: str, organization: str):
        self.token = token
        self.organization = organization

    def get_build(self, pipeline: str, build_number: str):
        # https://buildkite.com/docs/apis/rest-api/builds#get-a-build
        return benedict(self.get(f'https://api.buildkite.com/v2/organizations/{self.organization}/pipelines/{pipeline}/builds/{build_number}').json())

    def list_running_revision_builds(self, pipeline: str, rev: str):
        return self.get(f'https://api.buildkite.com/v2/organizations/{self.organization}/pipelines/{pipeline}/builds?state[]=scheduled&state[]=running&meta_data[ph_buildable_revision]={rev}').json()

    @backoff.on_exception(backoff.expo, Exception, max_tries=3, logger='', factor=3)
    def get(self, url: str):
        authorization = f'Bearer {self.token}'
        response = requests.get(url, allow_redirects=True, headers={'Authorization': authorization})
        if response.status_code != 200:
            raise Exception(f'Buildkite responded with non-OK status: {response.status_code}')
        return response

    # cancel a build. 'build' is a json object returned by API.
    def cancel_build(self, build):
        build = benedict(build)
        url = f'https://api.buildkite.com/v2/organizations/{self.organization}/pipelines/{build.get("pipeline.slug")}/builds/{build.get("number")}/cancel'
        authorization = f'Bearer {self.token}'
        response = requests.put(url, headers={'Authorization': authorization})
        if response.status_code != 200:
            raise Exception(f'Buildkite responded with non-OK status: {response.status_code}')


def format_url(url: str, name: Optional[str] = None):
    if name is None:
        name = url
    return f"\033]1339;url='{url}';content='{name}'\a\n"


def strip_emojis(s: str) -> str:
    return re.sub(r':[^:]+:', '', s).strip()
