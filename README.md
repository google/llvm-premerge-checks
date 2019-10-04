# Overview

This repository contains the configuration files for the merge guards for the LLVM project. It configures a cluster of build machines that are used to check all incoming commits to the LLVM project.

# Merge guards
TODO(@christiankuehnel): describe objective of merge guards

# Cluster overview
TODO(@christiankuehnel): describe how the cluster is set up

# Phabricator integration
TODO(@christiankuehnel): describe how this is integrated with Phabricator

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

# TODO list
* deploy Phabricator clone
* hook up first "clang-format" job
* deploy storage server, store build results there
* setup proper ingress server with SSL and user authentication
* Add missing configuration steps to these scripts
    * deploy and recover jenkings master configuration
* set up DNS names for agents, so the master can address them by name, not by IP

* change permissions to jenkins home folder by script
    * needs to be done before launching the Jenkins binary
    * probably add this to the jenkins.sh script in the docker container
