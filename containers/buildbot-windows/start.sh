# Checkout path is set to a fixed short value (e.g. c:\ws\src) to keep paths
# short as many tools break on Windows with paths longer than 250.

: ${WORKDIR:=/c/ws}
echo "WORKDIR $WORKDIR"
mkdir -p "$WORKDIR"

SCCACHE_DIR="$WORKDIR/sccache"
SCCACHE_IDLE_TIMEOUT="0"
SCCACHE_CACHE_SIZE=20G
sccache --start-server

whoami
env
tail -f