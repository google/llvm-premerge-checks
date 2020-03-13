This folder contains a set of scripts to mirror Phabricator *Revisions* to GitHub *Pull Requests*.

# Problem statement
The LLVM project performs code reviews on [Phabricator](https://reviews.llvm.org) and the source 
code is stored on [GitHub](https://github.com/llvm/llvm-project). While there are many nice CI 
system integrations available for GitHub (e.g. buildkite, CircleCI, GitHub Actions), there are not 
that many for Phabricator. The current setup of the pre-merge tests is quite some effort to maintain 
and does not scale well with additional build agents. User do not have access to the bulid status.

One of the challenges is that Phabricator maintains patches, that might not be based on a git 
commit. And even if they are based on a git commit, that commit might be local to the user and 
not available in the public repository.

# Proposal
Instead of integrating a CI system with Phabricator, move all the information to Github and trigger 
the builds from there.

1. Create a service that mirrors all Revisions form Phabricator into GitHub Pull Requests. 
1. Then use the usual CI integration for GitHub to build and test these revisions.
1. On Phabricator, add links to the builds.
1. At the end of the build, a script uploads the results to Phabricator (as we have it now).

If that works well, we can also use this to demonstrate the workflow of Github Pull Requests to the 
LLVM community.

# current status
The script currently does:

* Get the latest 10 Revisions from Phabricator for testing. 
* For each revision:
  * Create a local git branch `phab-Dxxxxx`
  * Create a local git branch `phab-diff-yyyyy` for every Diff of the Revision using the raw patch of each Diff.
  * Layer the diffs on top of each other in the `phab-Dxxxxxx` branch. 
  * Push the `phab-Dxxxxxx` branch to the [LLVM fork](https://github.com/ChristianKuehnel/llvm-project).
  * Create a [pull request](https://github.com/ChristianKuehnel/llvm-project/pulls) for each branch.
* The GitHub/Buildkite 
  [CI integration](https://buildkite.com/llvm-project/phabricator-pull-request-integration-prototype) 
  then triggers the builds for the PRs.

As this is a prototype, it currently has some shortcommings:
* I'm only looking at the 10 latest Revisions for testing.
* If a patch does not apply: just ignore it
* The Revision branches are always created from scratch, there is no incremental update.
* I run the script manually for testing, There are no automatic pull/push updates

# Work items

This is the list (and order) of the work items for this idea.
We will start with this on a fork of the LLVM repository running on my machine as cron job.
Cancel the effort if some thinks would not work or the community objects.

* [x] For each Revision create a branch. Create a PR from that.
* [x] Layer the diffs on top of each other in the git log.
* [ ] Figure out what to do with chained Revisions.
* [ ] Find a scalable way to reports results back to Phabricator. 
* [ ] Clean up old branches and PRs.
* [ ] Create pre-merge testing service to the cloud, trigger it with every change on Phabricator. 
      Also do regular full scans of Phabricator to catch everything lost in the triggers.
* [ ] Add more build machines to buildkite and move beta testers to new infrastructure.
* [ ] Move all pre-merge tests to new infrastructure.
* [ ] Find way to test new scripts/builders/configuration/... without annoying the users.
* [ ] Enable others to add more checks/builders as needed.


Optional: 
* [ ] Also sync Revisions that do not trigger Harbormaster at the moment and provide feedback as 
well.
* [ ] Find a way to copy the description and the comments from the Revision to the PR. 
* [ ] Create branches and PRs on LLVM repository, allow people to click the "Merge" button on the PR, 
reducing the manual work to land a patch. 