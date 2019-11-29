# escape=`

# use windows server core image
FROM gcr.io/llvm-premerge-checks/agent-windows

# install buildkite agent as described in the documentation
# https://buildkite.com/docs/agent/v3/windows
# Supply your agent token via the arguement "-token <mytoken" when building the image
ARG token
ENV buildkiteAgentToken="${token}"
ENV BUILDKITE_BUILD_PATH=C:\ws\bk
ENV BUILDKITE_AGENT_NAME=win-vs17

RUN powershell -NoProfile -InputFormat None -Command `
    Set-ExecutionPolicy Bypass -Scope Process -Force ; `
    iex ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/buildkite/agent/master/install.ps1'))

CMD "C:\buildkite-agent\bin\buildkite-agent.exe" start 