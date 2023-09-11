- [Overview](#overview)
- [Buildkite agents](#buildkite-agents)
- [Build steps](#build-steps)
- [Phabricator integration](#phabricator-integration)
  - [Life of a pre-merge check](#life-of-a-pre-merge-check)
  - [Cluster parts](#cluster-parts)
    - [Ingress and public addresses](#ingress-and-public-addresses)
  - [Enabled projects and project detection](#enabled-projects-and-project-detection)
  - [Agent machines](#agent-machines)
  - [Compilation caching](#compilation-caching)
- [Buildkite monitoring](#buildkite-monitoring)

# Overview

- [Buildkite](https://buildkite.com/llvm-project) orchestrates each build.

- multiple Linux and windows agents connected to Buildkite. Agents are run at
Google Cloud Platform.

- [small proxy service](/phabricator-proxy) that takes build requests from
[reviews.llvm.org](http://reviews.llvm.org) and converts them into Buildkite
build request. Buildkite job sends build results directly to Phabricator.

- every review creates a new branch in [fork of
llvm-project](https://github.com/llvm-premerge-tests/llvm-project).

![deployment diagram](http://www.plantuml.com/plantuml/proxy?src=https://raw.githubusercontent.com/google/llvm-premerge-checks/main/docs/deployment.plantuml)

# Buildkite agents

Agents are deployed in two clusters `llvm-premerge-checks` and `windows-cluster`.
The latter is for windows machines (as it is controlled on cluster level if
machines can run windows containers).

Container configurations are in ./containers and deployment configurations are
in ./kubernetes. Most important ones are:

- Windows agents: container `containers/buildkite-windows`, deployment `kubernetes/buildkite/windows.yaml`. TODO: at the moment Docker image is created and uploaded
from a windows machine (e.g. win-dev). It would be great to setup a cloudbuild.

- Linux agents: run tests for linux x86 config, container `containers/buildkite-linux`, deployment `kubernetes/buildkite/linux.yaml`.

- Service agents: run low CPU build steps (e.g. generate pipeline steps) container `containers/buildkite-linux`, deployment `kubernetes/buildkite/service.yaml`.

All deployments have a copy `..-test` to be used as a test playground to check
container / deployment changes before modifying "prod" setup.

# Build steps

Buildkite allows [dynamically define pipelines as the output of a
command](https://buildkite.com/docs/pipelines/defining-steps#dynamic-pipelines).
And most of pipelines use this pattern of running a script and using the
resulting yaml. E.g. script to run pull-request checks is llvm-project [.ci/generate-buildkite-pipeline-premerge](https://github.com/llvm/llvm-project/blob/main/.ci/generate-buildkite-pipeline-premerge). Thus any changes to steps to run should
go into that script.

We have a legacy set of scripts in `/scripts` in this repo but discourage new
use and development of them - they are mostly kept to make Phabricator integration
to function.

# Phabricator integration

Note: this section is about integrating with Phabricator that is now discouraged,
some things might already be renamed or straight broken as we moving to Pull Requests.

- [Harbormaster build plan](https://reviews.llvm.org/harbormaster/plan/5) the
Phabricator side these things were configured

- Herald [rule for everyone](https://reviews.llvm.org/H576) and for [beta
testers](https://reviews.llvm.org/H511). Note that right now there is no
difference between beta and "normal" builds.

- the [merge_guards_bot user](https://reviews.llvm.org/p/merge_guards_bot/)
account for writing comments.

## Life of a pre-merge check

When new diff arrives for review it triggers a Herald rule ("everyone" or "beta
testers").

That in sends an HTTP POST request to [**phab-proxy**](../phabricator-proxy)
that submits a new buildkite job **diff-checks**. All parameters from the
original request are put in the build's environment with `ph_` prefix (to avoid
shadowing any Buildkite environment variable). "ph_scripts_refspec" parameter
defines refspec of llvm-premerge-checks to use ("main" by default).

**diff-checks** pipeline
([create_branch_pipeline.py](../scripts/create_branch_pipeline.py))
downloads a patch (or series of patches) and applies it to a fork of the
llvm-project repository. Then it pushes a new state as a new branch (e.g.
"phab-diff-288211") and triggers "premerge-checks" on it (all "ph_" env
variables are passed to it). This new branch can now be used to reproduce the
build or by another tooling. Periodical **cleanup-branches** pipeline deletes
branches older than 30 days.

**premerge-checks** pipeline
([build_branch_pipeline.py](../scripts/build_branch_pipeline.py))
builds and tests changes on Linux and Windows agents. Then it uploads a
combined result to Phabricator.

## Cluster parts

### Ingress and public addresses

We use NGINX ingress for Kubernetes. Right now it's only used to provide basic
HTTP authentication and forwards all requests from load balancer to
[phabricator proxy](../phabricator-proxy) application.

Follow up to date docs to install [reverse
proxy](https://kubernetes.github.io/ingress-nginx/deploy/#gce-gke).

[cert-manager] is installed with helm https://cert-manager.io/docs/installation/helm/

helm install \
  cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --version v1.9.1 \
  --set installCRDs=true

We also have [certificate manager](https://cert-manager.io/docs/) and
[lets-encrypt configuration](../kubernetes/cert-issuer.yaml) in place, but they are
not used at the moment and should be removed if we decide to live with static IP.

HTTP auth is configured with k8s secret 'http-auth' in 'buildkite' namespace
(see [how to update auth](playbooks.md#update-http-auth-credentials)).

## Enabled projects and project detection

To reduce build times and mask unrelated problems, we're only building and
testing the projects that were modified by a patch.
[choose_projects.py](../scripts/choose_projects.py) uses manually maintained
[config file](../scripts/llvm-dependencies.yaml) to define inter-project
dependencies and exclude projects:

1. Get prefix (e.g. "llvm", "clang") of all paths modified by a patch.

1. Add all dependant projects.

1. Add all projects that this extended list depends on, completing the
dependency subtree.

1. Remove all disabled projects.

## Agent machines

All build machines are running from Docker containers so that they can be
debugged, updated, and scaled easily:

- [Linux](../containers/buildkite-premerge-debian/Dockerfile). We use
[Kubernetes deployment](../kubernetes/buildkite) to manage these agents.

- [Windows](../containers/agent-windows-buildkite/Dockerfile). At the moment they are run as
multiple individual VM instances.

See [playbooks](playbooks.md) how to manage and set up machines.

## Compilation caching

Each build is performed on a clean copy of the git repository. To speed up the
builds [ccache](https://ccache.dev/) is used on Linux and
[sccache](https://github.com/mozilla/sccache) on Windows.

# Buildkite monitoring

FIXME: does not work as of 2023-09-11. Those metrics could allow
  us to setup auto-scaling of machines to the current demend.

VM instance `buildkite-monitoring` exposes Buildkite metrics to GCP.
To set up a new instance:

1. Create as small Linux VM with full access to *Stackdriver Monitoring API*.

1. Follow instructions to [install monitoring
agent](https://cloud.google.com/monitoring/agent/install-agent) and [enable
statsd plugin](https://cloud.google.com/monitoring/agent/plugins/statsd).

1. Download recent release of
[buildkite-agent-metrics](https://github.com/buildkite/buildkite-agent-metrics/releases).

1. Run in SSH session:
```bash
chmod +x buildkite-agent-metrics-linux-amd64
nohup ./buildkite-agent-metrics-linux-amd64 -token XXXX -interval 30s -backend statsd &
```

Metrics are exported as "custom/statsd/gauge".

TODO: update "Testing scripts locally" playbook on how to run Linux build locally with Docker.
TODO: migrate 'builkite-monitoring' to k8s deployment.