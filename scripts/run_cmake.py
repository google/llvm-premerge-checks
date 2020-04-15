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

import argparse
from enum import Enum
from git import Repo
import os
import platform
import shutil
import subprocess
from typing import List, Dict
import yaml
import time
from choose_projects import ChooseProjects


class OperatingSystem(Enum):
    Linux = 'linux'
    Windows = 'windows'


class Configuration:

    def __init__(self, config_file_path: str):
        with open(config_file_path) as config_file:
            config = yaml.load(config_file, Loader=yaml.SafeLoader)
        self._environment = config['environment']  # type: Dict[OperatingSystem, Dict[str, str]]
        self.general_cmake_arguments = config['arguments']['general']  # type: List[str]
        self._specific_cmake_arguments = config['arguments']  # type: Dict[OperatingSystem, List[str]]
        self._default_projects = config['default_projects']  # type: Dict[OperatingSystem, str]
        self.operating_system = self._detect_os()  # type: OperatingSystem

    @property
    def environment(self) -> Dict[str, str]:
        return self._environment[self.operating_system.value]

    @property
    def specific_cmake_arguments(self) -> List[str]:
        return self._specific_cmake_arguments[self.operating_system.value]

    @property
    def default_projects(self) -> str:
        return self._default_projects[self.operating_system.value]

    @staticmethod
    def _detect_os() -> OperatingSystem:
        """Detect the current operating system."""
        if platform.system() == 'Windows':
            return OperatingSystem.Windows
        return OperatingSystem.Linux


def _select_projects(config: Configuration, projects: str, repo_path: str) -> str:
    """select which projects to build.

    if projects == "default", a default configuraiton will be used.

    if project == "detect", ChooseProjects is used to magically detect the projects
         based on the files modified in HEAD
    """
    if projects == "default" or projects is None or len(projects) == 0:
        return config.default_projects
    if projects == "detect":
        cp = ChooseProjects(repo_path)
        repo = Repo('.')
        patch = repo.git.diff("HEAD~1")
        enabled_projects = ';'.join(cp.choose_projects(patch))
        if enabled_projects is None or len(enabled_projects) == 0:
            enabled_projects = 'all'
        return enabled_projects
    return projects


def _create_env(config: Configuration) -> Dict[str, str]:
    """Generate the environment variables for cmake."""
    env = os.environ.copy()
    env.update(config.environment)
    return env


def _create_args(config: Configuration, llvm_enable_projects: str) -> List[str]:
    """Generate the command line arguments for cmake."""
    arguments = [
        os.path.join('..', 'llvm'),
        '-D LLVM_ENABLE_PROJECTS="{}"'.format(llvm_enable_projects),
    ]
    arguments.extend(config.general_cmake_arguments)
    arguments.extend(config.specific_cmake_arguments)

    # enable sccache
    if 'SCCACHE_DIR' in os.environ:
        arguments.extend([
            '-DCMAKE_C_COMPILER_LAUNCHER=sccache',
            '-DCMAKE_CXX_COMPILER_LAUNCHER=sccache',
        ])
    # enable ccache if the path is set in the environment
    elif 'CCACHE_PATH' in os.environ:
        arguments.extend([
            '-D LLVM_CCACHE_BUILD=ON',
            '-D LLVM_CCACHE_DIR={}'.format(os.environ['CCACHE_PATH']),
            '-D LLVM_CCACHE_MAXSIZE=20G',
        ])
    return arguments


def run_cmake(projects: str, repo_path: str, config_file_path: str = None, *, dryrun: bool = False):
    """Use cmake to configure the project.

    This version works on all operating systems.
    """
    if config_file_path is None:
        script_dir = os.path.dirname(__file__)
        config_file_path = os.path.join(script_dir, 'run_cmake_config.yaml')
    config = Configuration(config_file_path)

    build_dir = os.path.abspath(os.path.join(repo_path, 'build'))
    if not dryrun:
        secure_delete(build_dir)
        os.makedirs(build_dir)

    env = _create_env(config)
    llvm_enable_projects = _select_projects(config, projects, repo_path)
    print('Enabled projects: {}'.format(llvm_enable_projects))
    arguments = _create_args(config, llvm_enable_projects)
    cmd = 'cmake ' + ' '.join(arguments)
    
    # On Windows: configure Visutal Studio before running cmake
    if config.operating_system == OperatingSystem.Windows:
        # FIXME: move this path to a config file
        #   Or run it from the docker entrypoint
        cmd = r'"C:\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=amd64 -host_arch=amd64 && ' + cmd

    print('Running cmake with these arguments:\n{}'.format(cmd))
    if dryrun:
        print('Dryrun, not invoking CMake!')
    else:
        subprocess.check_call(cmd, env=env, shell=True, cwd=build_dir)
        _link_compile_commands(config, repo_path, build_dir)


def secure_delete(path: str):
    """Try do delete a local folder.

    Deleting folders on Windows can be tricky and frequently fails.
    In most cases this can be recovered by waiting some time and then trying again.
    """
    error_limit = 5
    while error_limit > 0:
        error_limit -= 1
        if not os.path.exists(path):
            return
        try:
            shutil.rmtree(path)
        except PermissionError:
            pass
        time.sleep(3)
    raise IOError('Could not delete build folder after several tries: {}'.format(path))


def _link_compile_commands(config: Configuration, repo_path: str, build_dir: str):
    """Link compile_commands.json from build to root dir"""
    if config.operating_system != OperatingSystem.Linux:
        return
    source_path = os.path.join(build_dir, 'compile_commands.json')
    target_path = os.path.join(repo_path, 'compile_commands.json')
    if os.path.exists(target_path):
        os.remove(target_path)
    os.symlink(source_path, target_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run CMake for LLVM.')
    parser.add_argument('projects', type=str, nargs='?', default='default')
    parser.add_argument('repo_path', type=str, nargs='?', default=os.getcwd())
    parser.add_argument('--dryrun', action='store_true')
    args = parser.parse_args()
    run_cmake(args.projects, args.repo_path, dryrun=args.dryrun)
