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

# Contributing

We're happy to get help on improving the infrastructure and workflows!

Please check [contibuting](docs/contributing.md) first.

[Development](docs/development.md) gives an overview how different parts
interact together.

[Playbooks](docs/playbooks.md) shows concrete examples how to, for example,
build and run agents locally.

# Additional Information

- [Playbooks](docs/playbooks.md) for installing/upgrading agents and testing
changes.

- [Log of the service
operations](https://github.com/google/llvm-premerge-checks/wiki/LLVM-pre-merge-tests-operations-blog)

# License

This project is licensed under the "Apache 2.0 with LLVM Exception" license. See
[LICENSE](LICENSE) for details.
