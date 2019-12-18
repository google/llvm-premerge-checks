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

1. Pick a GCP Windows image with Desktop Support.
    * pick a "persistent SSD" as boot Disk. This is much faster
    * Add a "local scratch SSD" and use it as you workspace. This is much faster.
1. Format the local SSD partition and use it as workspace.
1. install [Chocolately](https://chocolatey.org/docs/installation):
```bat
@"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))" && SET "PATH=%PATH%;%ALLUSERSPROFILE%\chocolatey\bin"
```
1. Install git: `choco install -y git`
1. Install [Docker Enterprise](https://docs.docker.com/ee/docker-ee/windows/docker-ee/) and reboot:
```powershell
Install-Module DockerMsftProvider -Force
Install-Package Docker -ProviderName DockerMsftProvider -Force
Restart-Computer
```
1. *optional:* install apps to help you work in the machine:
```powershell
choco install -y googlechrome vscode
```
1. Log out of the machine and log back in.
1. Repeat until success:
    1. Start "Docker Desktop" and let it install it's dependencies. 
    Then reboot manually, when the error message pops up.
    1. If you have trouble with the machine name: try to shorten it to 16 chars.
1. Configure the Docker credentials for GCP:
```powershell
gcloud components install docker-credential-gcr
docker-credential-gcr configure-docker
```
1. To build and run the current agent run:
```powershell
git clone https://github.com/google/llvm-premerge-checks
cd llvm-premerge-checks\containers
powershell .\build_run.ps1 agent-windows-jenkins
```
1. If you want to be able to push changes to github, you need to set up your github SSH keys and user name:
```powershell
ssh-keygen
git config --global user.name <your name>
git config --global user.email <your email>
```

To push push a new container run in `containers`:
```powershell
powershell .\build_deploy.ps1 <container-folder>
```

## Spawning a new windows agent

To spawn a new windows agent:

1. Go to the [GCP page](https://pantheon.corp.google.com/compute/instances?project=llvm-premerge-checks&instancessize=50) and pick a new number for the agent.
1. Update the machine name in `kubernetes/windows_agent_create.sh`.
1. Run `kubernetes/windows_agent_create.sh`
1. Go to the [GCP page](https://pantheon.corp.google.com/compute/instances?project=llvm-premerge-checks&instancessize=50) again 
1. login to the new machine via RDP (you probably need to set the i).
1. In the RDP session: run these commands in the CMD window to start the docker container:
```cmd
powershell 
Invoke-WebRequest -uri 'https://raw.githubusercontent.com/google/llvm-premerge-checks/master/kubernetes/windows_agent_bootstrap.ps1' -OutFile windows_agent_bootstrap.ps1
.\windows_agent_bootstrap.ps1
```

## Testing scripts locally

Build and run agent docker image `sudo build_run.sh agent-debian-testing-clang8-ssd /bin/bash`.

Within a container set environment variables similar to [pipeline](https://github.com/google/llvm-premerge-checks/blob/master/Jenkins/Phabricator-pipeline/Jenkinsfile).

Additionally set `WORKSPACE`, `PHID` and `DIFF_ID` parameters. Set `CONDUIT_TOKEN` with your personal one from `https://reviews.llvm.org/settings/user/<USERNAME>/page/apitokens/`.