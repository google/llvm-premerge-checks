# Status

No known issues :see_no_evil:

# Overview

The *pre-merge checks* for the [LLVM project](http://llvm.org/) are a
[continuous integration
(CI)](https://en.wikipedia.org/wiki/Continuous_integration) workflow. The
workflow checks the patches the developers upload to the [LLVM
Phabricator](https://reviews.llvm.org) instance.

*Phabricator* (https://reviews.llvm.org) is the code review tool in the LLVM
project.

The workflow checks the patches before a user merges them to the master branch -
thus the term *pre-merge testing**. When a user uploads a patch to the LLVM
Phabricator, Phabricator triggers the checks and then displays the results.

The CI system checks the patches **before** a user merges them to the master
branch. This way bugs in a patch are contained during the code review stage and
do not pollute the master branch. The more bugs the CI system can catch during
the code review phase, the more stable and bug-free the master branch will
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
* patch in Phabricator, **or** your patch can be applied to the master branch.

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

# Contributing

We're happy to get help on improving the infrastructure and workflows!

Please check [contibuting](docs/contributing.md) first.

[Development](docs/development.md) gives an overview how different parts
interact together.

[Playbooks](docs/playbooks.md) shows concrete examples how to, for example,
build and run agents locally.

If you have any questions please contact by [mail](mailto:goncahrov@google.com)
or find user "goncharov" on [LLVM Discord](https://discord.gg/VrcTUs).

# Additional Information

- [Playbooks](docs/playbooks.md) for installing/upgrading agents and testing
changes.

- [Log of the service
operations](https://github.com/google/llvm-premerge-checks/wiki/LLVM-pre-merge-tests-operations-blog)

# License

This project is licensed under the "Apache 2.0 with LLVM Exception" license. See
[LICENSE](LICENSE) for details.
