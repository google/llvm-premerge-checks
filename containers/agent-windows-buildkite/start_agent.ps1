$Env:buildkiteAgentToken = [IO.File]::ReadAllText("C:\credentials\buildkite-token.txt")

#Set-ExecutionPolicy Bypass -Scope Process -Force 
iex ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/buildkite/agent/master/install.ps1'))

# use the name of the host machine as name for the agent in buildkite
$env:BUILDKITE_AGENT_NAME="win-vs17 $env:PARENT_HOSTNAME"

C:\buildkite-agent\bin\buildkite-agent.exe start --tags "os=windows"