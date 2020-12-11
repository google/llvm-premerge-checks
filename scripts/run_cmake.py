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
import logging
from enum import Enum
from git import Repo
import os
import platform
import shutil
import subprocess
import stat
import sys
from typing import List, Dict
import yaml

from choose_projects import ChooseProjects


class OperatingSystem(Enum):
    Linux = 'linux'
    Windows = 'windows'


class Configuration:
    """Configuration for running cmake.

    The data is mostly read from the file `run_cmake_config.yaml`
    residing in the same folder as this script.
    """

    def __init__(self, config_file_path: str):
        with open(config_file_path) as config_file:
            config = yaml.load(config_file, Loader=yaml.SafeLoader)
        self._environment = config['environment']  # type: Dict[OperatingSystem, Dict[str, str]]
        self.general_cmake_arguments = config['arguments']['general']  # type: List[str]
        self._specific_cmake_arguments = config[
            'arguments']  # type: Dict[OperatingSystem, List[str]]
        self.operating_system = self._detect_os()  # type: OperatingSystem

    @property
    def environment(self) -> Dict[str, str]:
        return self._environment[self.operating_system.value]

    @property
    def specific_cmake_arguments(self) -> List[str]:
        return self._specific_cmake_arguments[self.operating_system.value]

    @property
    def default_projects(self) -> str:
        """Get string of projects enabled by default.

        This returns all projects in the mono repo minus the project that were
        excluded for the current platform.
        """
        cp = ChooseProjects(None)
        return ';'.join(cp.get_all_enabled_projects())

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
        logging.debug(f'diff {patch}')
        enabled_projects = ';'.join(cp.choose_projects(patch))
        if enabled_projects is None or len(enabled_projects) == 0:
            logging.warning('Cannot detect affected projects. Enable all projects')
            enabled_projects = cp.get_all_enabled_projects()
        return enabled_projects
    return projects


def _create_env(config: Configuration) -> Dict[str, str]:
    """Generate the environment variables for cmake."""
    env = os.environ.copy()
    env.update(config.environment)
    return env


def _create_args(config: Configuration, llvm_enable_projects: str, use_cache: bool) -> List[str]:
    """Generate the command line arguments for cmake."""
    arguments = [
        os.path.join('..', 'llvm'),
        '-D LLVM_ENABLE_PROJECTS="{}"'.format(llvm_enable_projects),
    ]
    arguments.extend(config.general_cmake_arguments)
    arguments.extend(config.specific_cmake_arguments)

    if use_cache:
        if 'SCCACHE_DIR' in os.environ:
            logging.info("using sccache")
            arguments.extend([
                '-DCMAKE_C_COMPILER_LAUNCHER=sccache',
                '-DCMAKE_CXX_COMPILER_LAUNCHER=sccache',
            ])
        # enable ccache if the path is set in the environment
        elif 'CCACHE_DIR' in os.environ:
            logging.info("using ccache")
            arguments.extend([
                '-D LLVM_CCACHE_BUILD=ON',
            ])
    return arguments


def run(projects: str, repo_path: str, config_file_path: str = None, *, dry_run: bool = False):
    """Use cmake to configure the project and create build directory.

    Returns build directory and path to created artifacts.

    This version works on Linux and Windows.

    Returns: exit code of cmake command, build directory, path to CMakeCache.txt, commands.
    """
    commands = []
    if config_file_path is None:
        script_dir = os.path.dirname(__file__)
        config_file_path = os.path.join(script_dir, 'run_cmake_config.yaml')
    config = Configuration(config_file_path)

    build_dir = os.path.abspath(os.path.join(repo_path, 'build'))
    if not dry_run:
        secure_delete(build_dir)
        os.makedirs(build_dir)
        commands.append("rm -rf build")
        commands.append("mkdir build")
        commands.append("cd build")
    for k, v in config.environment.items():
        commands.append(f'export {k}="{v}"')
    env = _create_env(config)
    llvm_enable_projects = _select_projects(config, projects, repo_path)
    print('Enabled projects: {}'.format(llvm_enable_projects), flush=True)
    arguments = _create_args(config, llvm_enable_projects, True)
    cmd = 'cmake ' + ' '.join(arguments)

    print('Running cmake with these arguments:\n{}'.format(cmd), flush=True)
    if dry_run:
        print('Dry run, not invoking CMake!')
        return 0, build_dir, [], []
    result = subprocess.call(cmd, env=env, shell=True, cwd=build_dir)
    commands.append('cmake ' + ' '.join(_create_args(config, llvm_enable_projects, False)))
    commands.append('# ^note that compiler cache arguments are omitted')
    _link_compile_commands(config, repo_path, build_dir, commands)
    return result, build_dir, [os.path.join(build_dir, 'CMakeCache.txt')], commands


def secure_delete(path: str):
    """Try do delete a local folder.

    Handle read-only files.
    """
    if not os.path.exists(path):
        return

    def del_rw(action, name, exc):
        os.chmod(name, stat.S_IWRITE)
        os.unlink(name)

    shutil.rmtree(path, onerror=del_rw)


def _link_compile_commands(config: Configuration, repo_path: str, build_dir: str, commands: List[str]):
    """Link compile_commands.json from build to root dir"""
    if config.operating_system != OperatingSystem.Linux:
        return
    source_path = os.path.join(build_dir, 'compile_commands.json')
    target_path = os.path.join(repo_path, 'compile_commands.json')
    if os.path.exists(target_path):
        os.remove(target_path)
    os.symlink(source_path, target_path)
    commands.append(f'ln -s $PWD/compile_commands.json ../compile_commands.json')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run CMake for LLVM.')
    parser.add_argument('projects', type=str, nargs='?', default='default')
    parser.add_argument('repo_path', type=str, nargs='?', default=os.getcwd())
    parser.add_argument('--dryrun', action='store_true')
    parser.add_argument('--log-level', type=str, default='WARNING')
    args = parser.parse_args()
    logging.basicConfig(level=args.log_level, format='%(levelname)-7s %(message)s')
    result, _, _, _ = run(args.projects, args.repo_path, dry_run=args.dryrun)
    sys.exit(result)
