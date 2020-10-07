# escape=`

# use windows server core image
ARG agent_windows_version=latest
FROM gcr.io/llvm-premerge-checks/agent-windows-vs2019:${agent_windows_version}

RUN choco install -y handle --checksum 524E61547C8E26608CDA1B11B6E9471616CCCC48530F6E7EC9131EABF839357E
COPY start_agent.ps1 C:\scripts\
COPY pre-checkout.bat c:\buildkite-agent\hooks\
COPY unlock_path.ps1 c:\scripts
CMD "powershell C:\scripts\start_agent.ps1"