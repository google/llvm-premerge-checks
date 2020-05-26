c:\credentials\buildkite-env.ps1
# Install Buildkite agent.
iex ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/buildkite/agent/master/install.ps1'))
C:\buildkite-agent\bin\buildkite-agent.exe start