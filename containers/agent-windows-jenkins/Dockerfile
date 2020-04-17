# escape=`

# use windows server core image
ARG agent_windows_version
FROM gcr.io/llvm-premerge-checks/agent-windows-vs2019:2

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

# temporary directory, can be mounted on host if required 
VOLUME C:\Temp

# start swarm plugin
COPY start_agent.ps1 c:\jenkins
ENTRYPOINT ["C:\\BuildTools\\Common7\\Tools\\VsDevCmd.bat", "&&", "powershell.exe", "-NoLogo", "-ExecutionPolicy", "Bypass", "C:\\jenkins\\start_agent.ps1"]
