# Monitoring the LLVM main branch

This document proposes a design to improve the stability of the LLVM main branch
for use in pre-merge testing. 

## Background

TODO explain background:
  * Phab only has diffs, we need to apply these on a git base revision.
  * Many of the base revisions are broken. 
  * pre-merge fails due to unrelated issues.
  * goal: reduce % of broken revisions by getting them fixed faster


## High-level Design

  We propose to run a Buildbot worker on the main branch with the same
  Docker image we're using for pre-merge testing. That worker shall check all
  commits to main for build and test failures with regards to the configuration
  we're using for pre-merge testing. Whenever these builds fails, Buildbot 
  notifies the commiters and gives them the opportunity to fix or revert their
  patch. 
  
  This is much faster than a having a human investigate the issue and notify the
  committers. By having faster feedback the main branch is broken for fewer
  revisions and this the probability of a false-positive pre-merge test is lower.

## Machine setup

We would deploy another container as part of the existing Kubernetes cluster for
pre-merge testing. The image would be based on 
[buildkite-premerge-debian]https://github.com/google/llvm-premerge-checks/blob/main/containers/buildkite-premerge-debian/Dockerfile)
, and we would just add the things needed for the Buildbot agent by resuing the
setup of an existing worker (e.g. 
[clangd-ubuntu-clang](https://github.com/llvm/llvm-zorg/blob/main/Buildbot/google/docker/Buildbot-clangd-ubuntu-clang/Dockerfile.)
).

## Build configuration

The Buildbot worker should run as much of the pre-merge testing scripts as
possible to get the results as close as we can to that of what we would see
happen in pre-merge testing.

Currently we're running these steps on Buildkite to check the main branch:

``` bash
export SRC=${BUILDKITE_BUILD_PATH}/llvm-premerge-checks
rm -rf ${SRC}
git clone --depth 1 https://github.com/google/llvm-premerge-checks.git "${SRC}"
cd "${SRC}"
git fetch origin "${ph_scripts_refspec:-master}":x
git checkout x
cd "$BUILDKITE_BUILD_CHECKOUT_PATH"
pip install -q -r ${SRC}/scripts/requirements.txt
${SRC}/scripts/pipeline_main.py | tee /dev/tty | buildkite-agent pipeline upload
```

We should run similar steps on Buildbot by creating a new `BuilderFactory` to
the [existing
list](https://github.com/llvm/llvm-zorg/tree/main/zorg/buildbot/builders) and
then configuring it [as
usual](https://github.com/llvm/llvm-zorg/blob/main/buildbot/osuosl/master/config/builders.py).


## Open questions

1. Do we actually need to create a `BuilderFactory` or can we also just run a
   shell script?
2. How can we quickly test and iterate on the Python scripting? How can we run
   our own Buildbot master for testing?
3. The current solution by only wrapping the existing pre-merge testing scripts
   will not result in nice build steps as the other builders are producing as
   buildkite does not have that concept. Is that an issue?
4. We do need to check out the pre-merge testing config and scripts form another
   git repo. Is that an issue?