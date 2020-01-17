$Env:buildkiteAgentToken = [IO.File]::ReadAllText("C:\credentials\buildkite-token.txt")

#Set-ExecutionPolicy Bypass -Scope Process -Force 
iex ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/buildkite/agent/master/install.ps1'))

C:\buildkite-agent\bin\buildkite-agent.exe start --tags "os=windows"