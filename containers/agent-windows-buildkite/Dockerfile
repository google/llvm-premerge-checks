# escape=`

# use windows server core image
ARG agent_windows_version=latest
FROM gcr.io/llvm-premerge-checks/agent-windows-vs2019:${agent_windows_version}

COPY start_agent.ps1 C:\scripts\
CMD "powershell C:\scripts\start_agent.ps1"