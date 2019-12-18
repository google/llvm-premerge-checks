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
RUN powershell -NoProfile -InputFormat None -Command `
    (New-Object Net.WebClient).DownloadFile("https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe", "$env:Temp\GoogleCloudSDKInstaller.exe") ; `
    & $env:Temp\GoogleCloudSDKInstaller.exe ; `
    del $env:Temp\GoogleCloudSDKInstaller.exe
VOLUME C:\credentials
VOLUME C:\Temp

# start swarm plugin
COPY start_agent.bat c:\jenkins
CMD c:\jenkins\start_agent.bat