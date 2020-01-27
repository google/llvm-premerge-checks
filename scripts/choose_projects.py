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
import fileinput
import json
import logging
import os
import sys
from typing import Dict, List, Set, Tuple

from unidiff import PatchSet

# TODO: get this from llvm/CMakeLists.txt in "set(LLVM_ALL_PROJECTS ..."
all_projects = 'clang;clang-tools-extra;compiler-rt;debuginfo-tests;libc;libclc;libcxx;libcxxabi;libunwind;lld;lldb;llgo;mlir;openmp;parallel-libs;polly;pstl'.split(';')
# TODO: why do I need to add this manually???
all_projects.append('llvm')

# file where dependencies are defined
SCRIPT_DIR = os.path.dirname(__file__)
DEPENDENCIES_FILE = os.path.join(SCRIPT_DIR, 'project_dependencies.json')


def main() -> int:
    parser = argparse.ArgumentParser(description='Compute the projects affected by a change.')
    parser.add_argument('llvmdir', default='.')
    args = parser.parse_args()

    llvm_dir = os.path.abspath(os.path.expanduser(args.llvmdir))
    logging.info('Scanning LLVM in {}'.format(llvm_dir))
    match_projects_dirs(llvm_dir, all_projects)
    changed_files = get_changed_files()
    changed_projects, unmapped_changes = get_changed_projects(changed_files)

    if unmapped_changes:
        logging.warning('There were changes that could not be mapped to a project.'
                        'Building all projects instead!')
        print('all')
        return 0

    affected_projects = get_affected_projects(changed_projects)
    print(';'.join(affected_projects))
    return 0


def load_usage_map() -> Dict[str,List[str]]:
    """Load the dependencies from a file and reverse the mapping."""
    logging.info('loading project dependencies from {}'.format(DEPENDENCIES_FILE))
    with open(DEPENDENCIES_FILE) as dependencies_file:
        depencies = json.load(dependencies_file)
    usages = dict()
    for user, used_list in depencies.items():
        for used in used_list:
            usages.setdefault(used,[]).append(user)
    return usages


def match_projects_dirs(llvm_dir: str, all_projects: List[str]):
    """Make sure that all projects are folders in the LLVM dir.
    Otherwise we can't create the regex...
    """
    subdirs = os.listdir(llvm_dir)
    for project in all_projects:
        if project not in subdirs:
            logging.error('Project no found in LLVM root folder: {}'.format(project))
            sys.exit(1)


def get_changed_files() -> Set[str]:
    """get list of changed files from the patch from STDIN."""
    patch = PatchSet(sys.stdin)
    changed_files = set({f.path for f in patch.modified_files + patch.added_files + patch.removed_files})

    logging.info('Files modified by this patch:\n  ' + '\n  '.join(sorted(changed_files)))
    return changed_files


def get_changed_projects(changed_files: Set[str]) -> Tuple[Set[str],bool]:
    """Get list of projects affected by the change."""
    changed_projects = set()
    unmapped_changes = False
    for changed_file in changed_files:
        project = changed_file.split('/',maxsplit=1)
        if project is None or project[0] not in all_projects:
            unmapped_changes = True
            logging.warning('Could not map file to project: {}'.format(changed_file))
        else:
            changed_projects.add(project[0])

    logging.info('Projects directly modified by this patch:\n  ' + '\n  '.join(sorted(changed_projects)))
    return changed_projects, unmapped_changes


def get_affected_projects(changed_projects:Set[str]) -> Set[str]:
    """Compute transitive closure of affected projects based on the dependencies between the projects."""
    affected_projects=set(changed_projects)
    last_len = -1
    usages = load_usage_map()
    while len(affected_projects) != last_len:
        last_len = len(affected_projects)
        changes = set()
        for project in affected_projects:
            if project in usages:
                changes.update(usages[project])
        affected_projects.update(changes)

    logging.info('Projects affected by this patch:')
    logging.info('  ' + '\n  '.join(sorted(affected_projects)))

    return affected_projects


if __name__ == "__main__":
    logging.basicConfig(filename='choose_projects.log', level=logging.INFO)
    sys.exit(main())