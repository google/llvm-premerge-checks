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
#    choco install visualstudio2017buildtools -y `
#        --version 15.9.17.0  `
#        --package-parameters --quiet --norestart `
#            --add Microsoft.VisualStudio.Workload.VCTools `
#            --add Microsoft.VisualStudio.Component.VC.ATLMFC

# install other tools as described in https://llvm.org/docs/GettingStartedVS.html
RUN choco install -y git & `
    choco install -y cmake --version 3.15.4 & `
    choco install -y python2 & `
    choco install -y gnuwin32-coreutils.install & `
    choco install -y ninja

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