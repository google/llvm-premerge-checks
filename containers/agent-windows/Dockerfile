# escape=`

# use windows server core image
ARG version=ltsc2019
FROM mcr.microsoft.com/windows/servercore:$version

# install chocolately as package manager
RUN powershell -Command `
    iex ((new-object net.webclient).DownloadString('https://chocolatey.org/install.ps1')) ; `
    choco feature disable --name showDownloadProgress

# install Visual Studio build tools
RUN powershell -NoProfile -InputFormat None -Command `
    choco install visualcpp-build-tools `
        --version 15.0.26228.20170424 -y; `
    Write-Host 'Waiting for Visual C++ Build Tools to finish'; `
    Wait-Process -Name vs_installer

# install other tools as described in https://llvm.org/docs/GettingStartedVS.html
RUN choco install -y git & `
    choco install -y cmake --version 3.15.4 & `
    choco install -y python2 & `
    choco install -y gnuwin32-coreutils.install & `
    choco install -y ninja

# Install Java and Jenkins swarm plugin
#RUN choco install -y choco install jre8
RUN powershell -NoProfile -InputFormat None -Command `
   mkdir c:\jenkins ; `
   cd \jenkins ; `
   Invoke-WebRequest -OutFile swarm-client.jar -Uri https://repo.jenkins-ci.org/releases/org/jenkins-ci/plugins/swarm-client/3.17/swarm-client-3.17.jar

# use this drive to store the worksapce
VOLUME W:

# Start developer command prompt with any other commands specified.
#ENTRYPOINT "C:\Program Files (x86)\Microsoft Visual Studio\2017\BuildTools\Common7\Tools\VsDevCmd.bat" &
# Default to PowerShell if no other command specified.
CMD ["cmd"]