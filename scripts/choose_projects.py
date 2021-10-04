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

"""Compute the LLVM_ENABLE_PROJECTS for cmake from diff.

This script will compute which projects are affected by the diff provided via STDIN.
It gets the modified files in the patch, assigns them to projects and based on a
project dependency graph it will get the transitively affected projects.
"""

import argparse
import logging
import os
import platform
import sys
from typing import Any, Dict, List, Set, TextIO, Tuple, Optional, Union
from unidiff import PatchSet  # type: ignore
import yaml

class ChooseProjects:
    # file where dependencies are defined
    SCRIPT_DIR = os.path.dirname(__file__)
    DEPENDENCIES_FILE = os.path.join(SCRIPT_DIR, 'llvm-dependencies.yaml')

    def __init__(self, llvm_dir: Optional[str]):
        self.llvm_dir = llvm_dir
        self.defaultProjects: Dict[str, Dict[str, str]] = {}
         # List of projects this project depends on, transitive closure.
         # E.g. compiler-rt -> [llvm, clang].
        self.dependencies: Dict[str,Set[str]] = {}
        # List of projects that depends on this project. It's a full closure.
        # E.g. llvm -> [clang, libcxx, ...]
        self.usages: Dict[str, Set[str]] = dict()
        self.all_projects: List[str] = ['all']
        self.config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self):
        logging.info('loading project config from {}'.format(self.DEPENDENCIES_FILE))
        with open(self.DEPENDENCIES_FILE) as dependencies_file:
            self.config = yaml.load(dependencies_file, Loader=yaml.SafeLoader)
        for k, v in self.config['dependencies'].items():
            self.dependencies[k] = set(v)
        # Closure of dependencies.
        while True:
            updated = False
            for s in self.dependencies.values():
                n = len(s)
                extend = set()
                for d in s:
                    extend.update(self.dependencies.get(d, set()))
                s.update(extend)
                if len(s) > n:
                    updated = True
            if not updated:
                break
        # Usages don't need to be closed as dependencies already are.
        for project, deps in self.dependencies.items():
            for d in deps:
                self.usages.setdefault(d, set()).add(project)
        logging.info(f'computed dependencies: {self.dependencies}')
        logging.info(f'computed usages: {self.usages}')
        self.all_projects = self.config['allprojects'].keys()

    def get_excluded(self, os: str) -> Set[str]:
        """Returns transitive closure for excluded projects"""
        return self.get_affected_projects(set(self.config['excludedProjects'].get(os, [])))

    def get_check_targets(self, projects: Set[str]) -> Set[str]:
        """Return the `check-xxx` targets to pass to ninja for the given list of projects"""
        if 'all' in projects:
            return set(["check-all"])
        targets = set()
        all_projects = self.config['allprojects']
        for project in projects:
            targets.update(set(all_projects.get(project, [])))
        return targets

    @staticmethod
    def _detect_os() -> str:
        """Detect the current operating system."""
        if platform.system() == 'Windows':
            return 'windows'
        return 'linux'

    def choose_projects(self, patch: str = None, os_name: Optional[str] = None) -> List[str]:
        """List all touched project with all projects that they depend on and also
        all projects that depend on them"""
        if self.llvm_dir is None:
            raise ValueError('path to llvm folder must be set in ChooseProject.')
        llvm_dir = os.path.abspath(os.path.expanduser(self.llvm_dir))
        logging.info('Scanning LLVM in {}'.format(llvm_dir))
        if not self.match_projects_dirs():
            logging.warning(f'{llvm_dir} does not look like a llvm-project directory')
            return self.get_all_enabled_projects(os_name)
        changed_files = self.get_changed_files(patch)
        changed_projects, unmapped_changes = self.get_changed_projects(changed_files)
        if unmapped_changes:
            logging.warning('There were changes that could not be mapped to a project.'
                            'Building all projects instead!')
            return self.get_all_enabled_projects(os_name)
        return self.extend_projects(changed_projects, os_name)

    def extend_projects(self, projects: Set[str], os_name : Optional[str] = None) -> List[str]:
        """Given a set of projects returns a set of projects to be tested taking
        in account exclusions from llvm-dependencies.yaml.
        """
        logging.info(f'projects: {projects}')
        if not os_name:
            os_name = self._detect_os()
        # Find all affected by current set.
        affected_projects = self.get_affected_projects(projects)
        logging.info(f'all affected projects(*) {affected_projects}')
        # Exclude everything that is affected by excluded.
        excluded_projects = self.get_excluded(os_name)
        logging.info(f'all excluded projects(*) {excluded_projects}')
        affected_projects = affected_projects - excluded_projects
        logging.info(f'effective projects list {affected_projects}')
        return sorted(affected_projects)

    def run(self):
        affected_projects = self.choose_projects()
        print("Affected:", ';'.join(affected_projects))
        print("Dependencies:", ';'.join(self.get_dependencies(affected_projects)))
        print("Check targets:", ';'.join(self.get_check_targets(affected_projects)))
        return 0

    def match_projects_dirs(self) -> bool:
        """Make sure that all projects are folders in the LLVM dir.
        """
        subdirs = os.listdir(self.llvm_dir)
        for project in self.all_projects:
            if project not in subdirs:
                logging.error('Project not found in LLVM root folder: {}'.format(project))
                return False
        return True

    @staticmethod
    def get_changed_files(patch_str: Union[str, TextIO, None] = None) -> Set[str]:
        """get list of changed files from the patch or from STDIN.
        e.g. ['compiler-rt/lib/tsan/CMakeLists.txt']"""
        if patch_str is None:
            patch_str = sys.stdin
        patch = PatchSet(patch_str)

        changed_files = set({f.path for f in patch.modified_files + patch.added_files + patch.removed_files})

        logging.info('Files modified by this patch:\n  ' + '\n  '.join(sorted(changed_files)))
        return changed_files

    def get_changed_projects(self, changed_files: Set[str]) -> Tuple[Set[str], bool]:
        """Get list of projects affected by the change."""
        logging.info("Get list of projects affected by the change.")
        changed_projects = set()
        unmapped_changes = False
        for changed_file in changed_files:
            project = changed_file.split('/', maxsplit=1)
            # There is no utils project.
            if project[0] == 'utils':
                continue
            if (project is None) or (project[0] not in self.all_projects):
                unmapped_changes = True
                logging.warning('Could not map file to project: {}'.format(changed_file))
            else:
                changed_projects.add(project[0])

        logging.info('Projects directly modified by this patch:\n  ' + '\n  '.join(sorted(changed_projects)))
        return changed_projects, unmapped_changes

    def get_affected_projects(self, changed_projects: Set[str]) -> Set[str]:
        """Compute transitive closure of affected projects based on the
        dependencies between the projects (including initially passed)."""
        affected: Set[str] = set(changed_projects)
        for p in changed_projects:
            affected.update(self.usages.get(p, set()))
        logging.info(f'added {affected - changed_projects} projects as they are affected')
        return affected

    def get_dependencies(self, projects: Set[str]) -> Set[str]:
        """Return transitive dependencies for a given projects (including the projects themself).

        These are the required dependencies for given `projects` so that they can be built.
        """
        affected: Set[str] = set(projects)
        for p in projects:
            affected.update(self.dependencies.get(p, set()))
        return affected

    def get_all_enabled_projects(self, os_name: Optional[str] = None) -> List[str]:
        """Get list of all not-excluded projects for current platform."""
        return self.extend_projects(set(self.all_projects), os_name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Compute the projects affected by a change. A patch file is expected on stdin.')
    parser.add_argument('--llvmdir', type=str, default='.')
    parser.add_argument('--log-level', type=str, default='INFO')
    args = parser.parse_args()
    logging.basicConfig(level=args.log_level, format='%(levelname)-7s %(message)s')
    logging.info(f'checking changes in {args.llvmdir}')
    chooser = ChooseProjects(args.llvmdir)
    sys.exit(chooser.run())
