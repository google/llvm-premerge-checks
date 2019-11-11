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
        --version 15.0.26228.20170424 -y --params "'/IncludeOptional'" ;`
    Write-Host 'Waiting for Visual C++ Build Tools to finish'; `
    Wait-Process -Name vs_installer

# install other tools as described in https://llvm.org/docs/GettingStartedVS.html
# and a few more that were not documented...
RUN choco install -y git & `
    choco install -y cmake --version 3.15.4 & `
    choco install -y python2 & `
    choco install -y gnuwin32-coreutils.install & `
    choco install -y ninja & `
    choco install -y grep & ` 
    choco install -y sed
RUN  pip install psutil    
RUN choco install -y diffutils

# configure Python encoding
ENV PYTHONIOENCODING=UTF-8

# update the path variable    
RUN powershell.exe -Command $path = $env:path + ';c:\Program Files (x86)\GnuWin32\bin;C:\Program Files\CMake\bin'; Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Environment\' -Name Path -Value $path

# use this drive to store the worksapce
VOLUME W:

# install buildkite agent as described in the documentation
# https://buildkite.com/docs/agent/v3/windows
# Supply your agent token via the arguement "-token <mytoken" when building the image
ARG token
ENV buildkiteAgentToken="${token}"
ENV BUILDKITE_BUILD_PATH=W:\buildkite
ENV BUILDKITE_AGENT_NAME=amd64-windows-visualstudio2017

RUN powershell -NoProfile -InputFormat None -Command `
    Set-ExecutionPolicy Bypass -Scope Process -Force ; `
    iex ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/buildkite/agent/master/install.ps1'))

# support long file names during git checkout
RUN git config --system core.longpaths true

CMD "C:\buildkite-agent\bin\buildkite-agent.exe" start