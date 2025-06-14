# This Repository is Deprecated

> [!IMPORTANT]
> LLVM now uses Github Actions natively and the infrastructure definitions have
> moved. The infrastructure is now available in https://github.com/llvm/llvm-zorg
> under the `premerge` folder with associated scripts in
> https://github.com/llvm/llvm-project under the `.ci` folder. The github workflow
> definitions are under the `.github/workflows` folder.

# Old Content

This repo is holding VM configurations for machine cluster and scripts to run pre-merge tests triggered by http://reviews.llvm.org.

As LLVM project has moved to Pull Requests and Phabricator will no longer trigger builds, this repository will likely be gone.

[Pull request migration schedule](https://discourse.llvm.org/t/pull-request-migration-schedule/71595).

# Overview

Presentation by Louis Dione on LLVM devmtg 2021 https://youtu.be/B7gB6van7Bw

[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/B7gB6van7Bw/0.jpg)](https://www.youtube.com/watch?v=B7gB6van7Bw)

The *pre-merge checks* for the [LLVM project](http://llvm.org/) are a
[continuous integration
(CI)](https://en.wikipedia.org/wiki/Continuous_integration) workflow. The
workflow checks the patches the developers upload to the [LLVM
Phabricator](https://reviews.llvm.org) instance.

*Phabricator* (https://reviews.llvm.org) is the code review tool in the LLVM
project.

The workflow checks the patches before a user merges them to the main branch -
thus the term *pre-merge testing**. When a user uploads a patch to the LLVM
Phabricator, Phabricator triggers the checks and then displays the results.

The CI system checks the patches **before** a user merges them to the main
branch. This way bugs in a patch are contained during the code review stage and
do not pollute the main branch. The more bugs the CI system can catch during
the code review phase, the more stable and bug-free the main branch will
become. <sup>[citation needed]()</sup>

This repository contains the configurations and script to run pre-merge checks
for the LLVM project.

## Feedback

If you notice issues or have an idea on how to improve pre-merge checks, please
create a [new issue](https://github.com/google/llvm-premerge-checks/issues/new)
or give a :heart: to an existing one.
 
## Sign up for beta-test

To get the latest features and help us developing the project, sign up for the
pre-merge beta testing by adding yourself to the ["pre-merge beta testing"
project](https://reviews.llvm.org/project/members/78/) on Phabricator.

## Opt-out

In case you want to opt-out entirely of pre-merge testing, add yourself to the
[OPT OUT project](https://reviews.llvm.org/project/view/83/).

If you decide to opt-out, please let us know why, so we might be able to improve
in the future.

# Requirements

The builds are only triggered if the Revision in Phabricator is created/updated
via `arc diff`. If you update a Revision via the Web UI it will [not
trigger](https://secure.phabricator.com/Q447) a build.

To get a patch on Phabricator tested the build server must be able to apply the
patch to the checked out git repository. If you want to get your patch tested,
please make sure that either:

* You set a git hash as `sourceControlBaseRevision` in Phabricator which is
* available on the Github repository, **or** you define the dependencies of your
* patch in Phabricator, **or** your patch can be applied to the main branch.

Only then can the build server apply the patch locally and run the builds and
tests.

# Accessing results on Phabricator 

Phabricator will automatically trigger a build for every new patch you upload or
modify. Phabricator shows the build results at the top of the entry: ![build
status](docs/images/diff_detail.png)

The CI will compile and run tests, run clang-format and
[clang-tidy](docs/clang_tidy.md) on lines changed.

If a unit test failed, this is shown below the build status. You can also expand
the unit test to see the details: ![unit test
results](docs/images/unit_tests.png).

# Restarting Buildbots

Restarting the buildbots can be accomplished be deleting the pods running the
buildbots. Kubernetes will automatically recreate the pod, essentially
performing a restart.

To find the name of the buildbot pod, first make sure you are using the correct
cluster configuration with `kubectl` as the windows and linux builders are on
separate clusters.

Then, find the name of the buildbot pod:

```bash
kubectl get pods | grep buildbot
```

Once you have the name of the pod, you can run the following command:

```bash
kubectl delete pod <pod name from previous step>
```

This command might take a couple minutes to execute as kubernetes stops
the running processes/container. The new pod will then spin up and
everything will hopefully work after the restart.

# Contributing

We're happy to get help on improving the infrastructure and workflows!

Please check [contibuting](docs/contributing.md) first.

[Development](docs/development.md) gives an overview how different parts
interact together.

[Playbooks](docs/playbooks.md) shows concrete examples how to, for example,
build and run agents locally.

If you have any questions please contact by [mail](mailto:goncahrov@google.com)
or find user "goncharov" on [LLVM Discord](https://discord.gg/xS7Z362).

# Additional Information

- [Playbooks](docs/playbooks.md) for installing/upgrading agents and testing
changes.

- [Log of the service
operations](https://github.com/google/llvm-premerge-checks/wiki/LLVM-pre-merge-tests-operations-blog)

# License

This project is licensed under the "Apache 2.0 with LLVM Exception" license. See
[LICENSE](LICENSE) for details.
