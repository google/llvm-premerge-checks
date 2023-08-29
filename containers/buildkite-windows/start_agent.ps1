# TODO: remove after migrating scripts to LLVM repo.
git clone https://github.com/google/llvm-premerge-checks.git c:\llvm-premerge-checks
# Checkout path is set to a fixed short value (e.g. c:\ws\src) to keep paths
# short as many tools break on Windows with paths longer than 250.
$env:BUILDKITE_BUILD_CHECKOUT_PATH = "$env:BUILDKITE_BUILD_PATH\src"

# Install Buildkite agent.
iex ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/buildkite/agent/master/install.ps1'))
$env:SCCACHE_DIR="$env:BUILDKITE_BUILD_PATH\sccache"
$env:SCCACHE_IDLE_TIMEOUT="0"
Remove-Item -Recurse -Force -ErrorAction Ignore $env:SCCACHE_DIR
sccache --start-server
C:\buildkite-agent\bin\buildkite-agent.exe start
