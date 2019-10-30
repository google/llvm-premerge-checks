# escape=`

# use windows server core image
ARG version=ltsc2019
FROM mcr.microsoft.com/windows/servercore:$version

# install chocolately as package manager
RUN powershell -Command `
    iex ((new-object net.webclient).DownloadString('https://chocolatey.org/install.ps1')) ; `
    choco feature disable --name showDownloadProgress

# install Visual Studio build tools
RUN choco install -y --ignoredetectedreboot visualstudio2017buildtools --version 15.9.17.0  & exit 0

# TODO(ChristianKuehnel): 
# workaround used here: ignore errors of choco as it wants a reboot after the installation
# task: find out if there is a better way to handle the reboot request from choco than 
# ignoring the error code of the command

# TODO(ChristianKuehnel): 
# check if we can strip down the VS installation to speed up the installation 
# and reduce image size

# install other tools as described in https://llvm.org/docs/GettingStartedVS.html
RUN choco install -y git & `
    choco install -y cmake --version 3.15.4 & `
    choco install -y python2 & `
    choco install -y gnuwin32-coreutils.install

# clone llvm-project for testing
RUN md build & `
    cd build & `
    git clone --depth 1 https://github.com/llvm/llvm-project.git

# Start developer command prompt with any other commands specified.
#ENTRYPOINT C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\Common7\Tools\VsDevCmd.bat &&
# Default to PowerShell if no other command specified.
CMD ["powershell.exe", "-NoLogo", "-ExecutionPolicy", "Bypass"]