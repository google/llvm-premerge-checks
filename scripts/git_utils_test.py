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
import scripts.git_utils as git_utils

def assertForkIsSynced(upstreamPath, forkPath):
    upstream = git.Repo(path=upstreamPath)
    fork = git.Repo(path=forkPath)
    forkBranches = {}
    for b in fork.branches:
      forkBranches[b.name] = b
    for b in upstream.branches:
      assert b.name in forkBranches
      assert b.commit.hexsha == forkBranches[b.name].commit.hexsha, f'branch {b.name} head'

def forkIsSynced(upstreamPath, forkPath) -> bool:
    upstream = git.Repo(path=upstreamPath)
    fork = git.Repo(path=forkPath)
    forkBranches = {}
    for b in fork.branches:
      forkBranches[b.name] = b
    for b in upstream.branches:
      if b.name not in forkBranches:
        return False
      if b.commit.hexsha != forkBranches[b.name].commit.hexsha:
        return False
    return True

def add_simple_commit(remote, name: str):
    with open(os.path.join(remote.working_tree_dir, name), 'wt') as f:
      f.write('first line\n')
    remote.index.add([os.path.join(remote.working_tree_dir, name)])
    remote.index.commit(name)

def test_sync_branches(tmp_path):
    upstreamRemote = os.path.join(tmp_path, 'upstreamBare')
    forkRemote = os.path.join(tmp_path, 'forkBare')
    git.Repo.init(path=upstreamRemote, bare=True)
    git.Repo.init(path=forkRemote, bare=True)
    upstreamPath = os.path.join(tmp_path, 'upstream')
    forkPath = os.path.join(tmp_path, 'fork')
    upstream = git.Repo.clone_from(url=upstreamRemote, to_path=upstreamPath)
    add_simple_commit(upstream, '1')
    upstream.git.push('origin', 'main')
    fork = git.Repo.clone_from(url=forkRemote, to_path=forkPath)
    fork.create_remote('upstream', url=upstreamRemote)
    git_utils.syncRemotes(fork, 'upstream', 'origin')
    fork.remotes.upstream.fetch()
    fork.create_head('main', fork.remotes.upstream.refs.main)
    fork.heads.main.checkout()

    # Sync init commit.
    git_utils.syncRemotes(fork, 'upstream', 'origin')
    assertForkIsSynced(upstreamRemote, forkRemote)

    # Add new change upstream.
    add_simple_commit(upstream, '2')
    upstream.git.push('--all')

    git_utils.syncRemotes(fork, 'upstream', 'origin')
    assertForkIsSynced(upstreamRemote, forkRemote)

    # Add new branch.
    upstream.create_head('branch1')
    upstream.heads['branch1'].checkout()
    add_simple_commit(upstream, '3')
    upstream.git.push('--all')

    git_utils.syncRemotes(fork, 'upstream', 'origin')
    assertForkIsSynced(upstreamRemote, forkRemote)

    # Add another branch commit.
    add_simple_commit(upstream, '4')
    upstream.git.push('--all')
    git_utils.syncRemotes(fork, 'upstream', 'origin')
    assertForkIsSynced(upstreamRemote, forkRemote)

    # Discard changes in fork.
    fork.remotes.origin.pull()
    fork.heads.main.checkout()
    add_simple_commit(fork, '5')
    fork.remotes.origin.push()

    upstream.remotes.origin.pull('main')
    upstream.heads.main.checkout()
    add_simple_commit(upstream, '6')
    upstream.remotes.origin.push()

    assert not forkIsSynced(upstreamRemote, forkRemote)
    assert os.path.isfile(os.path.join(fork.working_tree_dir, '5'))
    git_utils.syncRemotes(fork, 'upstream', 'origin')
    assertForkIsSynced(upstreamRemote, forkRemote)
    fork.git.pull('origin', 'main')
    fork.heads.main.checkout()
    assert not os.path.isfile(os.path.join(fork.working_tree_dir, '5'))
    assert os.path.isfile(os.path.join(fork.working_tree_dir, '6'))
