# escape=`

# use windows server core image
FROM gcr.io/llvm-premerge-checks/agent-windows

# install buildkite agent as described in the documentation
# https://buildkite.com/docs/agent/v3/windows
# Supply your agent token via the arguement "-token <mytoken" when building the image
ARG token
ENV BUILDKITE_BUILD_PATH=C:\ws\bk
ENV BUILDKITE_AGENT_NAME=win-vs17

COPY start_agent.ps1 C:\scripts\
CMD "powershell C:\scripts\start_agent.ps1"