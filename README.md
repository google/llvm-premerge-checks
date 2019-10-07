# Overview

This repository contains the configuration files for the merge guards for the LLVM project. It configures a cluster of build machines that are used to check all incoming commits to the LLVM project.

# Merge guards
TODO(@christiankuehnel): describe objective of merge guards

# Cluster overview

The cluster consists of these services:
* Jenkins build server: [http://jenkins.llvm-merge-guard.org]
* a set of Jenkins agents running the builds
* an nginx server with the build results/logs [http://jenkins.llvm-merge-guard.org]


# Jenkins-Phabricator integration
The Jenkins-Phabricator is based on the instructions provided with the [Phabricator-Jenkins Plugin](https://github.com/uber/phabricator-jenkins-plugin).

On the Phabricator side these things were configured:
* the Harbormaster [build plan](https://reviews.llvm.org/harbormaster/plan/3/)
* the Herald [rule](https://reviews.llvm.org/H511)

On the Jenkins side:
* in the Jenkins configuration page as explained in the instrucitons
* in the build [job](http://jenkins.llvm-merge-guard.org/job/Phabricator/)

There is no backup of the credentials. If you need to change it, generate a new one and update it in Jenkins and Phabricator.

# Playbooks

## deployment to a clean infrastructure
General remarks:
* GCP does not route any traffic to your services unless the service is "helthy". It might take a few minutes after startup before the services is classified as healthy. Until then you will only see some generic error message.

These are the steps to set up the build server on a clean infrastructure:
1. Configure the tools on your local machine: 
    ```bash
    ./setup.sh
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
1. ssh into the VM instance mounting the volume, find the mount point and then set
    ```bash
    # go to the mount point of the volume
    cd  /var/lib/kubelet/plugins/kubernetes.io/gce-pd/mounts/jenkins-home
    # change the permissions
    sudo chmod a+rwx 
    ```
1. push the docker images to gcr.io:
```bash
    cd containers/debian-testing-clang8
    ./build_deploy.sh
    
    cd ../jenkins-master
    ./build_deploy.sh
```
1. Deploy the stack: ``
    ```bash
    cd kubernetes
    ./deploy.sh
    ```
1. configure it

## handling SSH keys
The Jenkins server SSHs into the agents to start the agent application. Thus the master needs SSH access to the agent. To set this up:

1. Create an SSH key pair locally with `ssh-keygen`.
1. Copy the contents of `id_rsa` to the credentials section of the Jenkins UI.
1. Configure the agent in the Jenkins UI to use the new SSH keys you just uploaded.
1. Copy the contents of `id_rsa.pub` to `containers/<agent dir>/authorized keys`.
1. Rebuild and deploy the agents.

While this works, it does not fell like the perfect solution. I'm happy to get better ideas on this. 

# License
This project is licensed unter the "Apache 2.0 with LLVM Exception" license. See [LICENSE](LICENSE) for details.