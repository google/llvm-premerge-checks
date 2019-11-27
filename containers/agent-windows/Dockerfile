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
RUN choco install -y git
RUN choco install -y cmake --version 3.15.4
RUN choco install -y python2
RUN choco install -y ninja
RUN choco install -y gnuwin
RUN pip install psutil    

# configure Python encoding
ENV PYTHONIOENCODING=UTF-8

# update the path variable    
RUN powershell.exe -Command $path = $env:path + ';c:\Program Files (x86)\GnuWin32\bin;C:\Program Files\CMake\bin'; Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Environment\' -Name Path -Value $path

# use this folder to store the worksapce'
VOLUME C:\ws
WORKDIR C:\ws

# support long file names during git checkout
RUN git config --system core.longpaths true & `
    git config --global core.autocrlf false

# Start developer command prompt with any other commands specified.
#ENTRYPOINT "C:\Program Files (x86)\Microsoft Visual Studio\2017\BuildTools\Common7\Tools\VsDevCmd.bat" &
CMD cmd