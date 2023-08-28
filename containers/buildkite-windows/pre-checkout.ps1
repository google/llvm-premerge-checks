$env:BUILDKITE_BUILD_CHECKOUT_PATH="$env:BUILDKITE_BUILD_PATH/src"

echo "unlocking git"
taskkill /F /IM git.exe
rm -Force "$env:BUILDKITE_BUILD_CHECKOUT_PATH/.git/index.lock"
echo "BUILDKITE_BUILD_CHECKOUT_PATH: $env:BUILDKITE_BUILD_CHECKOUT_PATH"
echo "BUILDKITE_BUILD_PATH: $env:BUILDKITE_BUILD_PATH"
echo 'running processes (before)'
Get-Process | Where-Object {$_.Path -like "$env:BUILDKITE_BUILD_CHECKOUT_PATH*"} | Select-Object -ExpandProperty Path
echo "unlocking $env:BUILDKITE_BUILD_CHECKOUT_PATH"
handle -nobanner $env:BUILDKITE_BUILD_CHECKOUT_PATH
c:\scripts\unlock_path.ps1 $env:BUILDKITE_BUILD_CHECKOUT_PATH
echo 'running processes (after)'
Get-Process | Where-Object {$_.Path -like "$env:BUILDKITE_BUILD_CHECKOUT_PATH*"} | Select-Object -ExpandProperty Path

echo "BUILDKITE_REPO: $env:BUILDKITE_REPO"
if (Test-Path -Path $env:BUILDKITE_BUILD_CHECKOUT_PATH) {
    Set-Location -Path $env:BUILDKITE_BUILD_CHECKOUT_PATH
    $remoteUrl = git remote get-url origin
    echo "current remote URL: $remoteUrl"
    if ($remoteUrl -ne $env:BUILDKITE_REPO) {
        Write-Host "Remote URL does not match. Deleting and recreating the directory."
        Set-Location -Path "C:\"
        Remove-Item -Path $env:BUILDKITE_BUILD_CHECKOUT_PATH -Recurse -Force
    }
}

