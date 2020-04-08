# escape=`

# use windows server core image
ARG windows_version=ltsc2019
FROM mcr.microsoft.com/windows/servercore:${windows_version}

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

# install Visual Studio build tools
# VS2019 installation messes up something in the DotNet Framework. 
# Install this as last package
# expect exit code 1, as part of the mess up
RUN powershell -NoProfile -InputFormat None -Command `
    choco install -y visualstudio2019buildtools --version 16.5.2.0 `
        --package-parameters "--includeOptional" ; `
    exit 0

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

# Start developer command prompt with any other commands specified.
ENTRYPOINT "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\Common7\Tools\VsDevCmd.bat" &&
CMD powershell