# Copyright 2022 Google LLC
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

import git
import os
import logging

"""URL of upstream LLVM repository."""
LLVM_GITHUB_URL = 'ssh://git@github.com/llvm/llvm-project'
FORK_REMOTE_URL = 'ssh://git@github.com/llvm-premerge-tests/llvm-project'

def initLlvmFork(path: str) -> git.Repo:
  if not os.path.isdir(path):
      logging.info(f'{path} does not exist, cloning repository...')
      git.Repo.clone_from(FORK_REMOTE_URL, path)
  repo = git.Repo(path)
  # Remove index lock just in case.
  lock_file = f"{repo.working_tree_dir}/.git/index.lock"
  try:
    os.remove(lock_file)
    logging.info(f"removed {lock_file}")
  except FileNotFoundError:
    logging.info(f"{lock_file} does not exist")
  repo.remote('origin').set_url(FORK_REMOTE_URL)
  if 'upstream' not in repo.remotes:
    repo.create_remote('upstream', url=LLVM_GITHUB_URL)
  else:
    repo.remote('upstream').set_url(LLVM_GITHUB_URL)
  repo.git.fetch('--all')
  repo.git.clean('-ffxdq')
  repo.git.reset('--hard')
  repo.heads.main.checkout()
  repo.git.pull('origin', 'main')
  return repo

def syncLlvmFork(repo: git.Repo):
  repo.remote('origin').set_url(FORK_REMOTE_URL)
  if 'upstream' not in repo.remotes:
    repo.create_remote('upstream', url=LLVM_GITHUB_URL)
  repo.remote('upstream').set_url(LLVM_GITHUB_URL)
  syncRemotes(repo, 'upstream', 'origin')
  pass

def syncRemotes(repo: git.Repo, fromRemote, toRemote):
  """sync one remote from another"""
  repo.remotes[fromRemote].fetch()
  repo.git.push(toRemote, '-f', f'refs/remotes/{fromRemote}/*:refs/heads/*')
