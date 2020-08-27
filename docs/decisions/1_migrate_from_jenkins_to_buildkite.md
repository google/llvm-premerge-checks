## Goal

Migrate from the current build infrastructure on Jenkins. It works but:

- due to security concerns we cannot give users access to build interface and has to generate reports,copy artifacts etc. to mimic that.

- creating builds with new configurations, e.g. libc++ tests, requires a lot of cooperation between us and interested user.

- it's not possible for contributors to add new agents with different configurations. It also not clear how to make jenkins auto-scale number of agents.

- intial idea of "look we have a plugin to integrate Jenkins with Phabricator, that will make everything easy" does not hold: we have to interact with Conduit API and understand Phabricator quirks anyway to provide experience we want.

- it's hard to reproduce builds locally.

- relying only on Herald notifications does not seems to work ([#96](https://github.com/google/llvm-premerge-checks/issues/96))

**Non goal**

No changes to the current review workflow, e.g. run tests only if commit if is LGTM-ed [#60](https://github.com/google/llvm-premerge-checks/issues/60)).

## Alternatives considered

I have looked at [GitHub actions](https://help.github.com/en/actions) and [Buildkite](https://buildkite.com/docs/tutorials/getting-started) as alternatives to current setup.

While GitHub actions might be providing some interesting integration features with GitHub (maybe) I found it lacks some nice features that Buildkite have. Namely actions have:

- a limited support for shell and proposes javascript or docker containers as an "executor". That might not be as easy to debug or use to reproduce locally;

- a workflows that are more or less predefined, so to start specific steps for, e.g. 'clang-extra', we will likely need to start a job and detect within it that build is not needed. Buildkite give ability to dynamically generate steps as we go;

- very limited support for scaling / monitoring self-hosted agents ([issue](https://github.community/t5/GitHub-Actions/Self-hosted-runner-autoscaling/td-p/38416)) as well as [security issues](https://help.github.com/en/actions/hosting-your-own-runners/about-self-hosted-runners#self-hosted-runner-security-with-public-repositories).

## Proposed setup

Use buildkite pipelines and define them here, in llvm-premerge-checks repo. Diffs are going to be reflected in llvm-project fork. 
Hopefully buildkite alone should be enought for the common workflow. If it's not enough and/or there are some issues with phabricator-buildkite itegration that require client update (Phabricator, like we had with [Jenkins CSRF](https://github.com/google/llvm-premerge-checks/issues/163) we can introduce a separate "conrol" service. This service can also have a DB to collect stats, maintain cohesive history of every revisions, manage tricky workflow cases, and manage scaling of buildkite agents. As much as I don't wan't to maintain a new custom service it seems to be a better idea on a long run to work around missing features or having an ability to maintain a complex state or history.

### Common workflow
In the most simple case build will be triggered directly by the Harbormaster "buildkite" rule. Build pipeline will receive PHID / DiffID and:

- using the ID, communicate with the Phabricator and decide what diffs have to be applied to represent the change
- report back to Phabricator a link to the build in buildkite
- create a new branch in llvm-project fork and apply changes as a separate commits
- run "build planning" script that will generate further steps based on e.g. author or the diff (if she participates in beta-testing), affected paths, trottling...; there might be multiple steps like this further down the line.
- complete every build and attach relevant artifacts to the build; add linter comments
- report final build result back.

Later this workflow can be split into two steps: one will setup github branch and create a PR. Another one will be triggered by GitHub and report PR build status to it. There are challenges on who and when is going to communicate back to Phabricator results of the build. Alternatively we can create a separate pipeline for the reviews on GitHub.

### Cleaning up branches / PR

Branches / PR are going to be kept for some time (for example month) after review is completed of diff seems to be abandoned.
That can intially be done by running a scheduled build on buildkite that will list branches and communicate with Phabricator to understand what to be deleted. Alternatively we can use "control" as can easily maintain state and, thus can do less work and even get notifications from Phabricator about revisions being closed.

### Missed diffs

We see that in some cases [#96](https://github.com/google/llvm-premerge-checks/issues/96) phabricator does not trigger a build. But we still want to run them. We can periodically (hourly) list recent reviews in phabricator and figure out if builds already being run for them. I see two possibilites here:

1. (preferred) find a way to trigger a build for such missed revision. It's definitely possible to do from the UI / command line but missing from the conduit API. This way "Common workflow" will kick in and we will get a build.

2. start a build "out of bound" and attach a comment to the review, describing that situation and providing a link to the build status. Update comment when build is done.

### Custom worflows / build agents

This setup allows community to relatively easily add own agents with relevant "purpose-tag". E.g. libc++ contributors can add a new condition into the "build planning" step that will add new steps (including ones that target their own agents) if relevant code was modified.

### Autoscaling

Buildkite provides a [number of ways](https://buildkite.com/docs/tutorials/parallel-builds#auto-scaling-your-build-agents) to collect agent stats and decide if we should up or downscale the number of agents. Technically that can be probably be done as a separate build pipeline though for security reasons and ease of implementation we might want to do that either in "control" service or in a completely separate one that is not accessible publicly.
