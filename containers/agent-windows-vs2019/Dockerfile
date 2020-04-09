# escape=`
FROM mcr.microsoft.com/dotnet/framework/sdk:4.8-windowsservercore-ltsc2019

# Restore the default Windows shell for correct batch processing.
SHELL ["cmd", "/S", "/C"]

# Download the Build Tools bootstrapper.
ADD https://aka.ms/vs/16/release/vs_buildtools.exe C:\TEMP\vs_buildtools.exe

# Install Build Tools excluding workloads and components with known issues.
# Documentation for docker installation 
# https://docs.microsoft.com/en-us/visualstudio/install/build-tools-container?view=vs-2019
#
# Documentation on workloads 
# https://docs.microsoft.com/en-us/visualstudio/install/workload-component-id-vs-build-tools?view=vs-2019#c-build-tools
# 
# Documentation on flags
# https://docs.microsoft.com/en-us/visualstudio/install/use-command-line-parameters-to-install-visual-studio?view=vs-2019
RUN C:\TEMP\vs_buildtools.exe --quiet --wait --norestart --nocache `
    --installPath C:\BuildTools `
    --add Microsoft.VisualStudio.Workload.VCTools;includeOptional `
    --remove Microsoft.VisualStudio.Component.Windows10SDK.10240 `
    --remove Microsoft.VisualStudio.Component.Windows10SDK.10586 `
    --remove Microsoft.VisualStudio.Component.Windows10SDK.14393 `
    --remove Microsoft.VisualStudio.Component.Windows81SDK `
 || IF "%ERRORLEVEL%"=="3010" EXIT 0


# install chocolately as package manager
RUN powershell -NoProfile -InputFormat None -Command `
    iex ((new-object net.webclient).DownloadString('https://chocolatey.org/install.ps1')) ; `
    choco feature disable --name showDownloadProgress

# install tools as described in https://llvm.org/docs/GettingStartedVS.html
# and a few more that were not documented...
RUN choco install -y ninja
RUN choco install -y git
RUN choco install -y cmake --version 3.15.4
RUN choco install -y python3
RUN choco install -y gnuwin
RUN choco install -y sccache
RUN pip install psutil

# install python dependencies for the scripts
RUN pip install -r https://raw.githubusercontent.com/google/llvm-premerge-checks/master/scripts/requirements.txt

# configure Python encoding
ENV PYTHONIOENCODING=UTF-8

# update the path variable    
RUN powershell -NoProfile -InputFormat None  -Command `
    $path = $env:path + ';c:\Program Files (x86)\GnuWin32\bin;C:\Program Files\CMake\bin'; `
    Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Environment\' -Name Path -Value $path

# use this folder to store the worksapce'
VOLUME C:\ws
WORKDIR C:\ws

# support long file names during git checkout
RUN git config --system core.longpaths true & `
    git config --global core.autocrlf false

# Define the entry point for the docker container.
# This entry point starts the developer command prompt and launches the PowerShell shell.
ENTRYPOINT ["C:\\BuildTools\\Common7\\Tools\\VsDevCmd.bat", "&&", "powershell.exe", "-NoLogo", "-ExecutionPolicy", "Bypass"]

# FIXME: remove after testing
RUN choco install mc

# Start developer command prompt with any other commands specified.
# CMD powershell