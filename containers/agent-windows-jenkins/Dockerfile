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

# network storage for build results
VOLUME C:\results

# start swarm plugin
COPY start_agent.bat c:\jenkins
CMD c:\jenkins\start_agent.bat