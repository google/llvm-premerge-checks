# escape=`

# use windows server core image
FROM gcr.io/llvm-premerge-checks/agent-windows

# install java
RUN choco install -y openjdk

# get Jenkins swarm plugin
ENV SWARM_PLUGIN_URL="https://repo.jenkins-ci.org/releases/org/jenkins-ci/plugins/swarm-client/3.17/swarm-client-3.17.jar"
ENV SWARM_PLUGIN_JAR="C:\jenkins\swarm-client.jar"
RUN powershell -NoProfile -InputFormat None -Command `
    mkdir c:\jenkins ; `
    Invoke-WebRequest -Uri %SWARM_PLUGIN_URL% -OutFile %SWARM_PLUGIN_JAR%

# install gsutils to access Google Cloud Storage
RUN pip install gsutil
VOLUME C:\credentials

# install python dependencies for the scripts
RUN pip install -r https://raw.githubusercontent.com/google/llvm-premerge-checks/master/scripts/phabtalk/requirements.txt

# temporary directory, can be mounted on host if required 
VOLUME C:\Temp

# start swarm plugin
COPY start_agent.ps1 c:\jenkins
CMD powershell c:\jenkins\start_agent.ps1