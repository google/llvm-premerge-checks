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
