#/usr/bin/env bash

echo "BUILDKITE_BUILD_CHECKOUT_PATH: $BUILDKITE_BUILD_CHECKOUT_PATH"
echo "BUILDKITE_BUILD_PATH: $BUILDKITE_BUILD_PATH"
echo "unlocking git"
pkill -f git.exe
rm -f "$BUILDKITE_BUILD_CHECKOUT_PATH/.git/index.lock"
echo 'running processes (before)'
ps aux | grep "$BUILDKITE_BUILD_CHECKOUT_PATH"
echo "unlocking $BUILDKITE_BUILD_CHECKOUT_PATH"
handle -nobanner "$BUILDKITE_BUILD_CHECKOUT_PATH"
powershell /c/scripts/unlock_path.ps1 "$BUILDKITE_BUILD_CHECKOUT_PATH"
echo 'running processes (after)'
ps aux | grep "$BUILDKITE_BUILD_CHECKOUT_PATH"

echo "BUILDKITE_REPO: $BUILDKITE_REPO"
if [ -d "$BUILDKITE_BUILD_CHECKOUT_PATH" ]; then
    cd "$BUILDKITE_BUILD_CHECKOUT_PATH" || exit
    remoteUrl=$(git remote get-url origin)
    echo "current remote URL: $remoteUrl"
    if [ "$remoteUrl" != "$BUILDKITE_REPO" ]; then
        echo "Remote URL does not match. Deleting and recreating the directory."
        cd /c/
        rm -rf "$BUILDKITE_BUILD_CHECKOUT_PATH"
    fi
fi