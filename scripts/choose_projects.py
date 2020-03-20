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

"""Compute the LLVM_ENABLE_PROJECTS for Cmake from diff.

This script will compute which projects are affected by the diff proviaded via STDIN.
It gets the modified files in the patch, assings them to projects and based on a
project dependency graph it will get the transitively affected projects.
"""

import argparse
import logging
import os
import sys
from typing import Dict, List, Set, Tuple

from unidiff import PatchSet
import yaml

# TODO: We could also try to avoid running tests for llvm for projects that 
# only need various cmake scripts and don't actually depend on llvm (e.g. 
# libcxx does not need to run llvm tests, but may still need to include llvm).


class ChooseProjects:
    
    # file where dependencies are defined
    SCRIPT_DIR = os.path.dirname(__file__)
    DEPENDENCIES_FILE = os.path.join(SCRIPT_DIR, 'llvm-dependencies.yaml')
    # projects used if anything goes wrong
    FALLBACK_PROJECTS = ['all']

    def __init__(self, llvm_dir: str):
        self.llvm_dir = llvm_dir
        self.defaultProjects = dict()  # type: Dict[str, Dict[str, str]]
        self.dependencies = dict()  # type: Dict[str,List[str]]
        self.usages = dict()   # type: Dict[str,List[str]]
        self.all_projects = []  # type: List[str]
        self.excluded_projects = set()  # type: Set[str]
        self._load_config()

    def _load_config(self):
        logging.info('loading project config from {}'.format(self.DEPENDENCIES_FILE))
        with open(self.DEPENDENCIES_FILE) as dependencies_file:
            config = yaml.load(dependencies_file, Loader=yaml.SafeLoader)
        self.dependencies = config['dependencies']
        for user, used_list in self.dependencies.items():
            for used in used_list:
                self.usages.setdefault(used, []).append(user)
        self.all_projects = config['allprojects']
        self.excluded_projects = set(config['excludedProjects'])

    def choose_projects(self, patch: str = None) -> List[str]:
        llvm_dir = os.path.abspath(os.path.expanduser(self.llvm_dir))
        logging.info('Scanning LLVM in {}'.format(llvm_dir))
        if not self.match_projects_dirs():
            return self.FALLBACK_PROJECTS
        changed_files = self.get_changed_files(patch)
        changed_projects, unmapped_changes = self.get_changed_projects(changed_files)

        if unmapped_changes:
            logging.warning('There were changes that could not be mapped to a project.'
                            'Building all projects instead!')
            return self.FALLBACK_PROJECTS

        affected_projects = self.get_affected_projects(changed_projects)
        affected_projects = self.add_dependencies(affected_projects)
        affected_projects = affected_projects - self.excluded_projects
        return sorted(affected_projects)

    def run(self):
        print(';'.join(self.choose_projects()))
        return 0

    def match_projects_dirs(self) -> bool:
        """Make sure that all projects are folders in the LLVM dir.
        Otherwise we can't create the regex...
        """
        subdirs = os.listdir(self.llvm_dir)
        for project in self.all_projects:
            if project not in subdirs:
                logging.error('Project no found in LLVM root folder: {}'.format(project))
                return False
        return True

    @staticmethod
    def get_changed_files(patch_str: str = None) -> Set[str]:
        """get list of changed files from the patch from STDIN."""
        if patch_str is None:
            patch_str = PatchSet(sys.stdin)
        patch = PatchSet(patch_str)

        changed_files = set({f.path for f in patch.modified_files + patch.added_files + patch.removed_files})

        logging.info('Files modified by this patch:\n  ' + '\n  '.join(sorted(changed_files)))
        return changed_files

    def get_changed_projects(self, changed_files: Set[str]) -> Tuple[Set[str], bool]:
        """Get list of projects affected by the change."""
        changed_projects = set()
        unmapped_changes = False
        for changed_file in changed_files:
            project = changed_file.split('/', maxsplit=1)
            if project is None or project[0] not in self.all_projects:
                unmapped_changes = True
                logging.warning('Could not map file to project: {}'.format(changed_file))
            else:
                changed_projects.add(project[0])

        logging.info('Projects directly modified by this patch:\n  ' + '\n  '.join(sorted(changed_projects)))
        return changed_projects, unmapped_changes

    def get_affected_projects(self, changed_projects: Set[str]) -> Set[str]:
        """Compute transitive closure of affected projects based on the
        dependencies between the projects."""
        affected_projects = set(changed_projects)
        last_len = -1
        while len(affected_projects) != last_len:
            last_len = len(affected_projects)
            changes = set()
            for project in affected_projects:
                if project in self.usages:
                    changes.update(self.usages[project])
            affected_projects.update(changes)

        logging.info('Projects affected by this patch:')
        logging.info('  ' + '\n  '.join(sorted(affected_projects)))

        return affected_projects

    def add_dependencies(self, projects: Set[str]) -> Set[str]:
        """Return projects and their dependencies.

        All all dependencies to `projects` so that they can be built.
        """
        result = set(projects)
        last_len = -1
        while len(result) != last_len:
            last_len = len(result)
            changes = set()
            for project in result:
                if project in self.dependencies:
                    changes.update(self.dependencies[project])
            result.update(changes)
        return result


if __name__ == "__main__":
    logging.basicConfig(filename='choose_projects.log', level=logging.INFO)
    parser = argparse.ArgumentParser(
        description='Compute the projects affected by a change.')
    parser.add_argument('llvmdir', default='.')
    args = parser.parse_args()
    chooser = ChooseProjects(args.llvmdir)
    sys.exit(chooser.run())
