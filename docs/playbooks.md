- [Playbooks](#playbooks)
  * [Testing changes to the build scripts](#testing-changes-to-the-build-scripts)
  * [deployment to a clean infrastructure](#deployment-to-a-clean-infrastructure)
  * [creating basic authentication for reverse proxy](#creating-basic-authentication-for-reverse-proxy)
  * [Creating docker containers on Windows](#creating-docker-containers-on-windows)
  * [Spawning a new windows agent](#spawning-a-new-windows-agent)
    + [Buildkite](#buildkite)
    + [Jenkins](#jenkins)
  * [Testing scripts locally](#testing-scripts-locally)
  * [Custom environment variables](#custom-environment-variables)
- [Phabricator integration](#phabricator-integration)
  * [Herald](#herald)
  * [Harbormaster](#harbormaster)
  
# Playbooks

## Testing changes to the build scripts

It's recommended to test even smallest changes before committing them to the `master` branch.

1. Create a branch with your changes, e.g. "my-feature" and push it to origin.
2. Manually create a buildkite build in the pipeline you are updating and
    specify environment variable `scripts_branch="my-feature"` (see also [custom
    environment variables](#custom-environment-variables) for other options).
    To test "premerge-tests" pipeline pick an existing build and copy parameters
    from it, omitting "ph_target_phid", namely: "ph_build_id",
    "ph_buildable_diff", "ph_buildable_revision", "ph_initiator_phid" and
    "scripts_branch" variables.
    **Or** use Buildkite REST API, e.g. to run 'llvm-master-build':
    ```shell script
    curl -H "Authorization: Bearer MY-API-TOKEN" \
    -X POST "https://api.buildkite.com/v2/organizations/llvm-project/pipelines/llvm-master-build/builds" \
    -d '{"branch": "master", "commit": "HEAD", "env": {"scripts_branch": "my-feature"}}'
    ```
1. Wait for build to complete and maybe attach a link to it to your Pull
    Request.

## deployment to a clean infrastructure

General remarks:
* GCP does not route any traffic to your services unless the service is "healthy". It might take a few minutes after startup before the services is classified as healthy. Until then you will only see some generic error message.

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
    .\build_deploy.ps1 agent-windows-buildkite # or agent-windows-jenkins
    c:\llvm-premerge-check\scripts\windows_agent_start_buildkite.ps1 # or windows_agent_start_jenkins.ps1
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
   
### Jenkins
   1. Create `c:\credentials` folder with `build-agent-results_key.json` to access cloud storage copy from one of the existing machines.
   1. Run
   ```powershell
   git clone https://github.com/google/llvm-premerge-checks.git "c:\llvm-premerge-checks"
   C:\llvm-premerge-checks\scripts\windows_agent_start_buildkite.ps1 [-testing] [-version latest]
   ```

Metrics are exported as "custom/statsd/gauge".

## Testing scripts locally

Build and run agent docker image `sudo ./containers/build_run.sh agent-debian-testing-ssd /bin/bash`.

Within a container set environment variables similar to [pipeline](https://github.com/google/llvm-premerge-checks/blob/master/Jenkins/Phabricator-pipeline/Jenkinsfile).

Additionally set `WORKSPACE`, `PHID` and `DIFF_ID` parameters. Set `CONDUIT_TOKEN` with your personal one from `https://reviews.llvm.org/settings/user/<USERNAME>/page/apitokens/`.

## Custom environment variables

Buildkite pipelines have a number of custom environment variables one can set to change their behavior. That is useful to debug issues
or test changes. They are mostly used by pipleine generators, e.g. [build_master_pipeline](../scripts/buildkite/build_master_pipeline.py),
please refer to the source code for the details. These variables have `ph_` prefix and can be set with URL parameters in Harbormaster build.

Most commonly used are:

- `scripts_branch` ("master" by default): which branch of llvm-premerge-checks to use. This variable is also used in pipeline "bootstrap" in Buildkite interface.
- `ph_no_cache`: (if set to any value) clear compilation cache before the build.
- `ph_projects`: which projects to use, "detect" will look on diff to infer the projects, "default" selects all projects.
- `ph_notify_email`: comma-separated list of email addresses to be notified when build is complete.
- `ph_log_level` ("DEBUG", "INFO", "WARNING" (default) or "ERROR"): log level for build scripts. 
- `ph_no_filter_output` (if set to any value): do not filter output of `ninja all` and other commands from buildkite log.
- `ph_linux_agents`, `ph_windows_agents`: custom JSON constraints on agents. For example you might put one machine to a custom queue if it's errornous and send jobs to it with `ph_windows_agents="{{\"queue\": \"custom\"}}"`.
- `ph_skip_linux`, `ph_skip_windows` (if set to any value): skip build on this OS.

# Phabricator integration

The general flow for builds on Phabricator is:
1. A user uploads a *Diff* (=patch) to a *Revision* (set of Diffs with comments and buildstatus, ... ).
2. A *Herald* checks if one of the *rules* matches this event. 
3. You can use the rules to trigger a *Build* in *Harbormaster*.
4. Harbor sends an HTTP request to the Jenkins server.
5. Jenkins executes the build. In the last step of the build, a script is uploading the results to Phabricator.
6. Phabricator sets the build status and displays the results.

## Herald

We currently have these Herald rules to configure the builds:
* Triggering builds for everyone:
    * [H576](https://reviews.llvm.org/H576) This will only trigger for non-beta testers.
* Triggering the beta-test builds:
    * [H511](https://reviews.llvm.org/H511) or the beta testers, this is for testing new features.
    * [H552](https://reviews.llvm.org/H552) for all changes to MLIR (archived)
    * [H527](https://reviews.llvm.org/H527) for all changes to clang-extra-tools (archived)

You can *archive* a rule to disable it.

## Harbormaster

We have these build plans in Harbormaster:
* [Plan 4](https://reviews.llvm.org/harbormaster/plan/4/) Builds for everyone
* [Plan 3](https://reviews.llvm.org/harbormaster/plan/3/) Builds for beta testers
