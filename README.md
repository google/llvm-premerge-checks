# Overview

This repository contains the configuration files for the pre-merge checks for the LLVM project. This github project contains the documentation and the server configuration cluster of build machines that are used to check all incoming commits to the LLVM project.

# User documentation
See [docs/user_doc.md](docs/user_doc.md)

# Cluster overview

The cluster consists of these services:
* Jenkins build server: http://jenkins.llvm-merge-guard.org
* a set of Jenkins agents running the builds
* an nginx server with the build results/logs http://results.llvm-merge-guard.org

![deployment diagram](http://www.plantuml.com/plantuml/proxy?src=https://raw.githubusercontent.com/google/llvm-premerge-checks/master/docs/deployment.plantuml)

# Jenkins-Phabricator integration

The Jenkins-Phabricator is based on the instructions provided with the [Phabricator-Jenkins Plugin](https://github.com/uber/phabricator-jenkins-plugin).

On the Phabricator side these things were configured:
* the Harbormaster [build plan](https://reviews.llvm.org/harbormaster/plan/3/)
* the Herald [rule](https://reviews.llvm.org/H511)
* the [merge_guards_bot user](https://reviews.llvm.org/p/merge_guards_bot/) writing the comments

On the Jenkins side:
* in the Jenkins configuration page as explained in the instrucitons
* in the build [job](http://jenkins.llvm-merge-guard.org/job/Phabricator/)
* The Phabricator pluging is *not* used, as it's not flexible enough. Rather Phabricator just triggers the build via an HTTP request. The `arc patch` operations by scripts. The build feedback is also uploaded by scripts via the [harbormaster.sendmessage](https://secure.phabricator.com/conduit/method/harbormaster.sendmessage/) and [differential.revision.edit](https://secure.phabricator.com/conduit/method/differential.revision.edit/) APIs.

There is no backup of the credentials. If you need to change it, generate a new one and update it in Jenkins and Phabricator.

# Additional Information
* [Playbooks](docs/playbooks.md) for installing/upgrading
* [User documentation](docs/user_doc.md)
* [Log of the service operations](https://github.com/google/llvm-premerge-checks/wiki/LLVM-pre-merge-tests-operations-blog)

# License
This project is licensed unter the "Apache 2.0 with LLVM Exception" license. See [LICENSE](LICENSE) for details.
