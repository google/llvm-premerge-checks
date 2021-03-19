# escape=`
FROM mcr.microsoft.com/dotnet/framework/sdk:4.8-windowsservercore-ltsc2019

# Restore the default Windows shell for correct batch processing.
SHELL ["cmd", "/S", "/C"]

# Download the Build Tools bootstrapper.
ADD https://aka.ms/vs/16/release/vs_buildtools.exe C:\TEMP\vs_buildtools.exe

# Download channel for fixed install.
ARG CHANNEL_URL=https://aka.ms/vs/16/release/channel
ADD ${CHANNEL_URL} C:\TEMP\VisualStudio.chman

# Install Build Tools with C++ workload.
#   - Documentation for docker installation 
#     https://docs.microsoft.com/en-us/visualstudio/install/build-tools-container?view=vs-2019
#   - Documentation on workloads 
#     https://docs.microsoft.com/en-us/visualstudio/install/workload-component-id-vs-build-tools?view=vs-2019#c-build-tools
#   - Documentation on flags
#     https://docs.microsoft.com/en-us/visualstudio/install/use-command-line-parameters-to-install-visual-studio?view=vs-2019
RUN C:\TEMP\vs_buildtools.exe --quiet --wait --norestart --nocache `
    --channelUri C:\TEMP\VisualStudio.chman `
    --installChannelUri C:\TEMP\VisualStudio.chman `
    --installPath C:\BuildTools `
    --add Microsoft.VisualStudio.Workload.VCTools `
    --add Microsoft.VisualStudio.Component.VC.ATL `
    --includeRecommended `
    || IF "%ERRORLEVEL%"=="3010" EXIT 0

# Register DIA dll (Debug Interface Access) so it can be used to symbolize 
# the stack traces. Register dll for 32 and 64 bit.
# see https://developercommunity.visualstudio.com/content/problem/290674/msdia140dll-is-not-registered-on-vs2017-hosts.html
RUN regsvr32 /S "C:\BuildTools\DIA SDK\bin\amd64\msdia140.dll" & `
    regsvr32 /S "C:\BuildTools\DIA SDK\bin\msdia140.dll"

# install chocolately as package manager
RUN powershell -NoProfile -InputFormat None -Command `
    iex ((new-object net.webclient).DownloadString('https://chocolatey.org/install.ps1')) ; `
    choco feature disable --name showDownloadProgress

# install tools as described in https://llvm.org/docs/GettingStartedVS.html
# and a few more that were not documented...
RUN choco install -y ninja git python3 gnuwin
RUN choco install -y activeperl --version 5.28.0.20210106
RUN choco install -y cmake --version 3.15.4
# libcxx requires clang(-cl) to be available
RUN choco install -y sccache llvm
RUN pip install psutil

# install python dependencies for the scripts
RUN pip install -r https://raw.githubusercontent.com/google/llvm-premerge-checks/main/scripts/requirements.txt

# configure Python encoding
ENV PYTHONIOENCODING=UTF-8

# update the path variable    
# C:\Program Files\Git\usr\bin contains a usable bash and other unix tools.
RUN powershell -NoProfile -InputFormat None  -Command `
    $path = $env:path + ';C:\Program Files\CMake\bin;C:\Program Files\Git\usr\bin'; `
    Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Environment\' -Name Path -Value $path

# use this folder to store the worksapce'
VOLUME C:\ws
WORKDIR C:\ws

# support long file names during git checkout
RUN git config --system core.longpaths true & `
    git config --global core.autocrlf false

# Define the entry point for the docker container.
# This entry point starts the developer command prompt and launches the PowerShell shell.
#
# For running manually:
# C:\BuildTools\Common7\Tools\VsDevCmd.bat -arch=amd64 -host_arch=amd64
ENTRYPOINT ["C:\\BuildTools\\Common7\\Tools\\VsDevCmd.bat", "-arch=amd64", "-host_arch=amd64", "&&", "powershell.exe", "-NoLogo", "-ExecutionPolicy", "Bypass"]
