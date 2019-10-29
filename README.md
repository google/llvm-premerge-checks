# Overview

This repository contains the configuration files for the merge guards for the LLVM project. It configures a cluster of build machines that are used to check all incoming commits to the LLVM project.

# Pre-merge check vision for end of 2019
Maria is a developer working on a new idea for the LLVM project. When she submits a new diff to Phabricator (or updates an existing diff), the pre-merge checks are triggered automatically in the cloud. The pre-merge checks run in one configuration (amd64, Debian Testing, clang8) and comprise these steps:

* run CMake
* compile and link
* run check-all
* run clang-format and clang-tidy

Once a check is completed, the results are are attached to the Diff in Phabricator so that Maria is notified automatically with the results. Now she can check if the pre-merge checks passed and fix things as required. This way she does not have to run all checks on her local machine by hand. The first results are available within 2 hours of a change, but typically within 30 minutes.

As the pre-merge check cover the easy parts, a human reviewer can focus on the parts that the machine cannot cover. The pre-merge checks are optional, so a reviewer can also decide to ignore them if they do not work, take too long, or do not make sense. 
The build bots are still in place as they cover a much wider range of checks on the different platforms. So after Maria’s change has landed, the build bots might still find more bugs that were not found in the pre-merge checks. The number should be lower than what we have today though.

# Roadmap

During the LLVM developer meeting in Octover 2019, this was the raodmap we discussed:
* Until mid of November: preparation of the infrastructure for the beta testing
* Mid of November:
  * Announcement of the public beta testing phase on the LLVM mailing list.
  * Interested users are white-listed on the Herald rule.
* Until Januar: Beta testing for interested users.
* In January: 
  * Based on the feedback so far: enable pre-merge tests for all users.
  * Users can opt-out via a black-list in the Herald rule.
  * Start discussion with LLVM foundation on a permanent setup/maintenance for the pre-merge tests.

This roadmap is also reflected in the [Milestones](https://github.com/google/llvm-premerge-checks/milestones?direction=asc&sort=due_date&state=open).

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

# Playbooks

## deployment to a clean infrastructure

General remarks:
* GCP does not route any traffic to your services unless the service is "healthy". It might take a few minutes after startup before the services is classified as healthy. Until then you will only see some generic error message.

These are the steps to set up the build server on a clean infrastructure:
1. Configure the tools on your local machine:
    ```bash
    ./local_setup.sh
    ```
1. Delete the old cluster, if it still exists:
    ```bash
    cd kubernetes/cluster
    ./cluster_delete.sh
    ```
1. Create the cluster:
    ```bash
    cd kubernetes/cluster
    ./cluster_create.sh
    ```
1. Create the disk storage, if it does not yet exist:
    ```bash
    cd kubernetes/cluster
    ./disk_create.sh
    ```
1. SSH into the VM instance mounting the volume, find the mount point and then set
    ```bash
    # go to the mount point of the volume
    cd  /var/lib/kubelet/plugins/kubernetes.io/gce-pd/mounts/jenkins-home
    # change the permissions
    sudo chmod a+rwx
    ```
1. Push the docker images to gcr.io:
    ```bash
    cd containers
    #for each subfolder:
    ./build_deploy.sh <foldername>
    ```
1. Deploy the stack:
    ```bash
    cd kubernetes
    ./deploy.sh
    ```
1. Configure it

## creating basic authentication for reverse proxy

1. create auth file, based on [ingress-nginx documentation](https://github.com/kubernetes/ingress-nginx/tree/master/docs/examples/auth/basic)
    ```bash
    cd kubernetes/reverse-proxy
    htpasswd -c auth <username>
    # enter password at prompt
    # add more users as required
    kubectl create secret generic proxy-auth --from-file=auth --namespace=jenkins
    ```

# License
This project is licensed unter the "Apache 2.0 with LLVM Exception" license. See [LICENSE](LICENSE) for details.
