- [Playbooks](#playbooks)
  * [Testing scripts locally](#testing-scripts-locally)
  * [Testing changes before merging](#testing-changes-before-merging)
  * [Deployment to a clean infrastructure](#deployment-to-a-clean-infrastructure)
  * [Creating docker containers on Windows](#creating-docker-containers-on-windows)
  * [Spawning a new windows agent](#spawning-a-new-windows-agent)
    + [Buildkite](#buildkite)
  * [Custom environment variables](#custom-environment-variables)
  * [Update HTTP auth credentials](#update-http-auth-credentials)
  
# Playbooks

## Testing scripts locally

Build and run agent docker image `sudo ./containers/build_run.sh buildkite-premerge-debian /bin/bash`.

Set `CONDUIT_TOKEN` with your personal one from `https://reviews.llvm.org/settings/user/<USERNAME>/page/apitokens/`.

## Testing changes before merging

It's recommended to test even smallest changes before committing them to the `master` branch.

1. Create a pull request here.
1. Manually create a buildkite build in the pipeline you are updating and specify
    environment variable `ph_scripts_refspec="pull/123/head"`. Replace `123` 
    with your PR number. If you don't have access to create buildkite builds, 
    please ask a reviewer to do that.
  
   To test "premerge-tests" pipeline pick an existing build and copy "ph_"
   parameters from it, omitting "ph_target_phid" to skip updating an existing
   review.   
   
   See also [custom environment variables](#custom-environment-variables).
1. Wait for build to complete and maybe attach a link to it to your PR.

To test changes for the pipeline "setup" step please experiment on a copy first. 

## Deployment to a clean infrastructure

General remarks:
* GCP does not route any traffic to your services unless the service is
"healthy". It might take a few minutes after startup before the services is
classified as healthy. Until then, you will only see some generic error
message.

These are the steps to set up the build server on a clean infrastructure:  
1. Configure the tools on your local machine:
    ```bash
    ./local_setup.sh
    ```
   If you not running docker under your user, you might need to
   `sudo gcloud auth login --no-launch-browser && gcloud auth configure-docker`
   before running other commands under sudo.
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

## Creating docker containers on Windows

If you want to build/update/test docker container for Windows, you need to do this on a Windows machine.

**Note**: There is an existing *windows-development* machine that you can resume and use for development. Please stop it after use.

Here are the instructions to set up such a machine on GCP.

1. Pick a GCP Windows image with Desktop Support.
    * pick a "persistent SSD" as boot Disk. This is much faster
    * (optionally) add a "local scratch SSD" and use it as you workspace. This will make builds faster, but you **will not be able to stop** this instance and will have to kill and re-create it again.
    * make sure that you give enough permissions in "Identity and API access" to be able to e.g. push new docker images to GCR. 
    
1. Format the local SSD partition and use it as workspace.
1. install [Chocolately](https://chocolatey.org/docs/installation):
    ```powershell
    iex ((new-object net.webclient).DownloadString('https://chocolatey.org/install.ps1'))
    ```
1. Install development tools: `choco install -y git googlechrome vscode`
1. (optionally) If you want to be able to push changes to github, you need to set up your github SSH keys and user name:
    ```powershell
    ssh-keygen
    git config --global user.name <your name>
    git config --global user.email <your email>
    ```
1. Install [Docker Enterprise](https://docs.docker.com/ee/docker-ee/windows/docker-ee/) and reboot:
    ```powershell
    Install-Module DockerMsftProvider -Force
    Install-Package Docker -ProviderName DockerMsftProvider -Force
    Restart-Computer
    ```
1. Configure the Docker credentials for GCP:
    ```powershell
    gcloud init # set options according to ./k8s_config here
    gcloud components install docker-credential-gcr
    docker-credential-gcr configure-docker
    ```
1. To build and run the current agent run:
    ```powershell
    cd c:\
    git clone https://github.com/google/llvm-premerge-checks
    cd llvm-premerge-checks\containers
    .\build_deploy.ps1 agent-windows-buildkite
    c:\llvm-premerge-check\scripts\windows_agent_start_buildkite.ps1
    ```

## Spawning a new windows agent

To spawn a new windows agent:

1. Go to the [GCP page](https://pantheon.corp.google.com/compute/instances?project=llvm-premerge-checks&instancessize=50) and pick a new number for the agent.
1. Run `kubernetes/windows_agent_create.sh agent-windows-<number>`
1. Go to the [GCP page](https://pantheon.corp.google.com/compute/instances?project=llvm-premerge-checks&instancessize=50) again 
1. Login to the new machine via RDP (you will need a RDP client, e.g. Chrome app).
1. In the RDP session: run these commands in the CMD window under Administrator to bootstrap the Windows machine:
    ```powershell 
    Invoke-WebRequest -uri 'https://raw.githubusercontent.com/google/llvm-premerge-checks/master/scripts/windows_agent_bootstrap.ps1' -OutFile c:\windows_agent_bootstrap.ps1
    c:/windows_agent_bootstrap.ps1 -ssd
    ```
    Ignore the pop-up to format the new disk and wait for the machine to reboot.
    
### Buildkite
 
1. Create `c:\credentials` folder with file `buildkite-env.ps1`:
    ```powershell
    $Env:buildkiteAgentToken = "secret-token"
    $Env:BUILDKITE_AGENT_NAME = "w#"
    $Env:BUILDKITE_AGENT_TAGS = "queue=windows"
    $Env:CONDUIT_TOKEN = "conduit-api-token"
    ```
   Pleas mind the length of the agent name as it will be in path and might cause some tests to fail due to 260 character limit.
1. Clone scripts directory and start agent:
   ```powershell
   git clone https://github.com/google/llvm-premerge-checks.git C:\llvm-premerge-checks
   C:\llvm-premerge-checks\scripts\windows_agent_start_buildkite.ps1 [-workdir D:\] [-testing] [-version latest]
   ```
1. Add a task to start agent when machine restarts (make sure to pass correct parameters).
```
git clone https://github.com/google/llvm-premerge-checks.git C:\llvm-premerge-checks
schtasks.exe /create /tn "Start Buildkite agent" /ru SYSTEM /SC ONSTART /DELAY 0005:00 /tr "powershell -command 'C:\llvm-premerge-checks\scripts\windows_agent_start_buildkite.ps1 -workdir c:\ws'"
```

## Custom environment variables

Buildkite pipelines have a number of custom environment variables one can set to change their behavior. That is useful to debug issues
or test changes. They are mostly used by pipleine generators, e.g. [build_master_pipeline](../scripts/build_master_pipeline.py),
please refer to the source code for the details. These variables have `ph_` prefix and can be set with URL parameters in Harbormaster build.

Most commonly used are:

- `ph_scripts_refspec` ("master" by default): refspec branch of llvm-premerge-checks to use. This variable is also used in pipeline "bootstrap" in Buildkite interface.
- `ph_no_cache`: (if set to any value) clear compilation cache before the build.
- `ph_projects`: which projects to use, "detect" will look on diff to infer the projects, "default" selects all projects.
- `ph_notify_email`: comma-separated list of email addresses to be notified when build is complete.
- `ph_log_level` ("DEBUG", "INFO", "WARNING" (default) or "ERROR"): log level for build scripts. 
- `ph_no_filter_output` (if set to any value): do not filter output of `ninja all` and other commands from buildkite log.
- `ph_linux_agents`, `ph_windows_agents`: custom JSON constraints on agents. For example you might put one machine to a custom queue if it's errornous and send jobs to it with `ph_windows_agents="{{\"queue\": \"custom\"}}"`.
- `ph_skip_linux`, `ph_skip_windows` (if set to any value): skip build on this OS.

## Update HTTP auth credentials

To update e.g. buildkite http-auth:
```shell script
kubectl get secret http-auth -n buildkite -o yaml
# base64 decode it's data to 'auth'.
echo <data/auth from yaml> | base64 --decode > auth
# add / update passwords
htpasswd -b auth <user> <pass> 
# update secret
kubectl delete secret http-auth -n buildkite
kubectl create secret generic http-auth -n buildkite --from-file=./auth
```