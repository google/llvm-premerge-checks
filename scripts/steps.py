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

import io
import json
import logging
import os
from typing import List

from exec_utils import watch_shell
import yaml


def generic_linux(projects: str, check_diff: bool) -> List:
    if os.getenv('ph_skip_linux') is not None:
        return []
    scripts_refspec = os.getenv("ph_scripts_refspec", "master")
    no_cache = os.getenv('ph_no_cache') is not None
    log_level = os.getenv('ph_log_level', 'WARNING')
    linux_agents = {'queue': 'linux'}
    t = os.getenv('ph_linux_agents')
    if t is not None:
        linux_agents = json.loads(t)
    commands = [
        'set -euo pipefail',
        'ccache --clear' if no_cache else '',
        'ccache --zero-stats',
        'ccache --show-config',
        'mkdir -p artifacts',
        'dpkg -l >> artifacts/packages.txt',
        *checkout_scripts('linux', scripts_refspec),
        'set +e',
    ]

    if check_diff:
        commands.extend([
            '${SRC}/scripts/premerge_checks.py --check-clang-format --check-clang-tidy '
            f'--projects="{projects}" --log-level={log_level}',
        ])
    else:
        commands.extend([
            f'${{SRC}}/scripts/premerge_checks.py --projects="{projects}" --log-level={log_level} {filter_output}'
        ])
    commands.extend([
        'EXIT_STATUS=\\$?',
        'echo "--- ccache stats"',
        'ccache --print-stats',
        'ccache --show-stats',
        'exit \\$EXIT_STATUS',
    ])

    linux_buld_step = {
        'label': ':linux: x64 debian',
        'key': 'linux',
        'commands': commands,
        'artifact_paths': ['artifacts/**/*', '*_result.json', 'build/test-results.xml'],
        'agents': linux_agents,
        'timeout_in_minutes': 120,
        'retry': {'automatic': [
            {'exit_status': -1, 'limit': 2},  # Agent lost
            {'exit_status': 255, 'limit': 2},  # Forced agent shutdown
        ]},
    }
    return [linux_buld_step]


def generic_windows(projects: str) -> List:
    if os.getenv('ph_skip_windows') is not None:
        return []
    scripts_refspec = os.getenv("ph_scripts_refspec", "master")
    no_cache = os.getenv('ph_no_cache') is not None
    log_level = os.getenv('ph_log_level', 'WARNING')
    clear_sccache = 'powershell -command "sccache --stop-server; echo \\$env:SCCACHE_DIR; ' \
                    'Remove-Item -Recurse -Force -ErrorAction Ignore \\$env:SCCACHE_DIR; ' \
                    'sccache --start-server"'
    win_agents = {'queue': 'windows'}
    t = os.getenv('ph_windows_agents')
    if t is not None:
        win_agents = json.loads(t)
    windows_buld_step = {
        'label': ':windows: x64 windows',
        'key': 'windows',
        'commands': [
            clear_sccache if no_cache else '',
            'sccache --zero-stats',
            *checkout_scripts('windows', scripts_refspec),

            'powershell -command "'
            f'%SRC%/scripts/premerge_checks.py --projects=\'{projects}\' --log-level={log_level}; '
            '\\$exit=\\$?;'
            'sccache --show-stats;'
            'if (\\$exit) {'
            '  echo success;'
            '  exit 0; } '
            'else {'
            '  echo failure;'
            '  exit 1;'
            '}"',
        ],
        'artifact_paths': ['artifacts/**/*', '*_result.json', 'build/test-results.xml'],
        'agents': win_agents,
        'timeout_in_minutes': 90,
        'retry': {'automatic': [
            {'exit_status': -1, 'limit': 2},  # Agent lost
            {'exit_status': 255, 'limit': 2},  # Forced agent shutdown
        ]},
    }
    return [windows_buld_step]


def from_shell_output(command) -> []:
    """
    Executes shell command and parses stdout as multidoc yaml file, see
    https://buildkite.com/docs/agent/v3/cli-pipeline#pipeline-format.
    :param command: command, may include env variables
    :return: all 'steps' that defined in the result ("env" section is ignored).
             Non-zero exit code and malformed YAML produces empty result.
    """
    path = os.path.expandvars(command)
    logging.debug(f'invoking "{path}"')
    out = io.BytesIO()
    err = io.BytesIO()
    rc = watch_shell(out.write, err.write, path)
    logging.debug(f'exit code: {rc}, stdout: "{out.getvalue().decode()}", stderr: "{err.getvalue().decode()}"')
    steps = []
    if rc != 0:
        logging.error(
            f'{path} returned non-zero code {rc}, stdout: "{out.getvalue().decode()}", stderr: "{err.getvalue().decode()}"')
        return steps
    try:
        for part in yaml.safe_load_all(out.getvalue()):
            part.setdefault('steps', [])
            steps.extend(part['steps'])
    except yaml.YAMLError as e:
        logging.error(f'''"{path}" produced malformed YAML, exception:
{e}

stdout: >>>{out.getvalue().decode()}>>>''')
    return steps


def checkout_scripts(target_os: str, scripts_refspec: str) -> []:
    if target_os == 'windows':
        return [
            'set SRC=%BUILDKITE_BUILD_PATH%/llvm-premerge-checks',
            'rm -rf %SRC%',
            'git clone --depth 1 https://github.com/google/llvm-premerge-checks.git %SRC%',
            'cd %SRC%',
            f'git fetch origin "{scripts_refspec}":x',
            'git checkout x',
            'echo llvm-premerge-checks commit:',
            'git rev-parse HEAD',
            'pip install -q -r %SRC%/scripts/requirements.txt',
            'cd %BUILDKITE_BUILD_CHECKOUT_PATH%',
        ]
    return [
        'export SRC=${BUILDKITE_BUILD_PATH}/llvm-premerge-checks',
        'rm -rf ${SRC}',
        'git clone --depth 1 https://github.com/google/llvm-premerge-checks.git "${SRC}"',
        'cd ${SRC}',
        f'git fetch origin "{scripts_refspec}":x',
        'git checkout x',
        'echo "llvm-premerge-checks commit"',
        'git rev-parse HEAD',
        'pip install -q -r ${SRC}/scripts/requirements.txt',
        'cd "$BUILDKITE_BUILD_CHECKOUT_PATH"',
    ]
