# escape=`

# Agent image for LLVM org cluster.
# maybe mcr.microsoft.com/windows/servercore:ltsc2022?
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
RUN choco install -y ninja git
# Pin an older version of Python; the current Python 3.10 fails when
# doing "pip install" for the other dependencies, as it fails to find libxml
# while compiling some package.
RUN choco install -y python3 --version 3.9.7

# ActivePerl is currently not installable via Chocolatey, see
# http://disq.us/p/2ipditb. Install StrawberryPerl instead. Unfortunately,
# StrawberryPerl not only installs Perl, but also a redundant C/C++ compiler
# toolchain, and a copy of pkg-config which can cause misdetections for other
# built products, see
# https://github.com/StrawberryPerl/Perl-Dist-Strawberry/issues/11 for further
# details. Remove the redundant and unnecessary parts of the StrawberryPerl
# install.
RUN choco install -y strawberryperl && `
    rmdir /q /s c:\strawberry\c && `
    del /q c:\strawberry\perl\bin\pkg-config*

# libcxx requires clang(-cl) to be available
RUN choco install -y sccache llvm
RUN pip install psutil

# install python dependencies for the scripts
RUN pip install -r https://raw.githubusercontent.com/google/llvm-premerge-checks/main/scripts/requirements.txt

RUN curl -LO https://github.com/mstorsjo/llvm-mingw/releases/download/20220323/llvm-mingw-20220323-ucrt-x86_64.zip && `
    powershell Expand-Archive llvm-mingw-*-ucrt-x86_64.zip -DestinationPath . && `
    del llvm-mingw-*-ucrt-x86_64.zip && `
    ren llvm-mingw-20220323-ucrt-x86_64 llvm-mingw

# configure Python encoding
ENV PYTHONIOENCODING=UTF-8

# update the path variable    
# C:\Program Files\Git\usr\bin contains a usable bash and other unix tools.
# C:\llvm-mingw\bin contains Clang configured for mingw targets and
#     corresponding sysroots. Both the 'llvm' package (with Clang defaulting
#     to MSVC targets) and this directory contains executables named
#     'clang.exe' - add this last to let the other one have precedence.
#     To use these compilers, use the triple prefixed form, e.g.
#     x86_64-w64-mingw32-clang.
RUN powershell -Command `
    [System.Environment]::SetEnvironmentVariable('PATH', `
    [System.Environment]::GetEnvironmentVariable('PATH', 'machine') + ';C:\Program Files\Git\usr\bin;C:\llvm-mingw\bin', `
    'machine')

# support long file names during git checkout
RUN git config --system core.longpaths true & `
    git config --global core.autocrlf false

# For debugging of files beeing locked by some processes.
RUN choco install -y handle
COPY start_agent.ps1 C:\scripts\
COPY pre-checkout.bat c:\buildkite-agent\hooks\
COPY post-checkout.bat c:\buildkite-agent\hooks\
CMD ["powershell", "C:\\scripts\\start_agent.ps1"]