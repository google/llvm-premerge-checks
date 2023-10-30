echo "buildbot windows entrypoint"

: ${WORKDIR:=/c/ws}
echo "WORKDIR $WORKDIR"
mkdir -p "$WORKDIR"
echo "starting sccache"
export SCCACHE_DIR="$WORKDIR/sccache"
export SCCACHE_IDLE_TIMEOUT="0"
export SCCACHE_CACHE_SIZE=20G
sccache --start-server
sccache --show-stats

echo "configure buildbot"
mkdir -p /c/ws/buildbbot
buildbot-worker create-worker /c/ws/buildbot $BUILDBOT_ADDRESS $BUILDBOT_NAME $BUILDBOT_PASSWORD

echo "llvm-premerge-buildbots <llvm-premerge-buildbots@google.com>" > /c/ws/buildbot/info/admin
echo "Setup analogous to windows agent for Pull Request checks" > /c/ws/buildbot/info/host
echo "Windows ltsc2019, vs-2019, LLVM-16+" >> /c/ws/buildbot/info/host
echo "https://github.com/google/llvm-premerge-checks/blob/main/containers/buildbot-windows/Dockerfile" >> /c/ws/buildbot/info/host
echo "Get-WmiObject -Class Win32_Processor" >> /c/ws/buildbot/info/host
powershell.exe -c "Get-WmiObject -Class Win32_Processor" >> /c/ws/buildbot/info/host
echo "Get-WmiObject -Class Win32_Product" >> /c/ws/buildbot/info/host
powershell.exe -c "Get-WmiObject -Class Win32_Product" >> /c/ws/buildbot/info/host
$@