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

$@