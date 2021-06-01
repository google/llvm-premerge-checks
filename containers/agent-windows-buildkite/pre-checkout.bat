echo "pre-checkout: update scripts"
cd c:\llvm-premerge-checks
git pull
git rev-parse HEAD
powershell c:\llvm-premerge-checks\scripts\windows\pre-checkout.ps1