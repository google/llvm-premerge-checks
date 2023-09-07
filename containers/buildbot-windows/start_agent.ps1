# Checkout path is set to a fixed short value (e.g. c:\ws\src) to keep paths
# short as many tools break on Windows with paths longer than 250.
if ($null -eq $env:WORKDIR) { $env:WORKDIR = 'c:\ws' }

$env:SCCACHE_DIR="$env:WORKDIR\sccache"
$env:SCCACHE_IDLE_TIMEOUT="0"
Remove-Item -Recurse -Force -ErrorAction Ignore $env:SCCACHE_DIR
sccache --start-server

bash -c 'whoami && tail -f'