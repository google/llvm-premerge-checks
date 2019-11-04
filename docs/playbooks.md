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

## Creating docker containers on Windows

If you want to build/update/test docker container for Windows, you need to do this on a Windows machine. Here are the instructions to set up such a machine on GCP.

General hints:
* Use a GCP instance with "presistent SSD". This is much faster the the "persistent Disk".
* Try to avoid paths with white spaces in them.
* You need to [configure Internet Explorer to allow downloads](https://improveandrepeat.com/2018/03/internet-explorer-on-windows-server-enable-file-downloads/).
* Install Chrome, as Internet Explorer is a bit outdated. 
* Install a nice IDE to edit Dockerfiles and scripts. [VS Code](https://code.visualstudio.com/Download) is a good option.

1. Pick a GCP Windows image with Desktop Support.
2. Use the "Server Manager" application to install the "features":
    * Containers
    * HyperV
3. Install git with the default options: https://git-scm.com/download/win
4. git clone https://github.com/google/llvm-premerge-checks.git
    * Register your ssh keys on the windows machine on github if you intend to push changes.
5. Install docker: https://hub.docker.com/editions/community/docker-ce-desktop-windows
    * You will need a DockerHub account to download the installer.
    * Select "use Windows containers" during installation.
    * Start the "Docker Desktop" application, it will set up the required services for you.
6. Install [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/).
7. Install [gcloud](https://cloud.google.com/sdk/docs/quickstart-windows) and set it up according to the instructions. Then run `gcloud auth configure-docker` to authorize docker to push images.

Check your installation by running "docker build ." in the `containers/agent_windows` folder.