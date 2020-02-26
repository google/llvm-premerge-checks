# Pre-merge checks

The *pre-merge checks* for the [LLVM project](http://llvm.org/) are a [continuous integration (CI)](https://en.wikipedia.org/wiki/Continuous_integration) workflow. The workflow checks the patches the developers upload to the [LLVM Phabricator](https://reviews.llvm.org) instance. *Phabricator* is the code review tool in the LLVM project. The workflow checks the patches before a user merges them the master branch - thus the term *pre-merge testing*. When a user uploads a patch to the LLVM Phabricator, Phabricator triggers the checks and then displays the results. 

The *checks* comprise of these steps:

1. Checkout of the git repository
1. Apply the patch -- `arc patch`
1. Run Cmake -- see [run_cmake.sh](https://github.com/google/llvm-premerge-checks/blob/master/scripts/run_cmake.sh#L31) for details
1. Build the binaries -- `ninja all`
1. Run the test suite -- `ninja check-all`
1. Run clang-format and clang-tidy on the diff.

The checks are executed on one Linux platform (Debian Testing on amd64 with the clang-8 tool chain) at the moment. Builds and Test for Windows (amd64, Visual Studio 2017) are currently in beta testing. The plan is to add more platforms, in the future.

The CI system checks the patches **before** a user merges them to the master branch. This way bugs in a patch are contained during the code review stage and do not pollute the master branch. The more bugs the CI system can catch during the code review phase, the more stable and bug-free the master branch will become.

## Feedback

If you find any problems please raise an [issue on github](https://github.com/google/llvm-premerge-checks/issues).

## Opt out
In case you want to opt out entirely of pre-merge testing, add yourself to the [OPT OUT project](https://reviews.llvm.org/project/view/83/).

If you decide to opt out, please let us know why, so we might be able to improve in the future.

## Sign up for beta test

To get the latest features, sign up for the pre-merge beta testing by adding yourself to the ["pre-merge beta testing" project](https://reviews.llvm.org/project/members/78/) on Phabricator.

# Requirements

The builds are only triggered if the Revision in Phabricator is created/updated via `arc diff`. If you update a Revision via the Web UI it will [not trigger](https://secure.phabricator.com/Q447) a build. 

To get a patch on Phabricator tested the build server must be able to apply the patch to the checked out git repository. If you want to get your patch tested, please make sure that that either:

* You set a git hash as `sourceControlBaseRevision` in Phabricator which is available on the Github repository,
* **or** you define the dependencies of your patch in Phabricator, 
* **or** your patch can be applied to the master branch.

Only then can the build server apply the patch locally and run the builds and tests.

# Integration in Phabricator

Once you're signed up, Phabricator will automatically trigger a build for every new patch you upload or every existing patch you modify. Phabricator shows the build results at the top of the entry:
![build status](images/diff_detail.png)

Bot will compile and run tests, run clang-format and [clang-tidy](docs/clang_tidy.md) on lines changed. 

If a unit test failed, this is shown below the build status. You can also expand the unit test to see the details:
![unit test results](images/unit_tests.png)

The build logs are stored for 90 days and automatically deleted after that.

You can also trigger a build manually by using the "Run Plan Manually" link on the [Harbormaster page](https://reviews.llvm.org/harbormaster/plan/3/) and entering a revision ID in the pop-up window.

# Reporting issues

If you notice any bugs, please create a [new issue](https://github.com/google/llvm-premerge-checks/issues/new).

# Contributing

We're happy to get help on improving the infrastructure and the workflows. If you're interested please contact [Christian Kühnel](mailto:kuhnel@google.com).
