# Based ob https://dandraka.com/2019/08/13/find-and-kill-processes-that-lock-a-file-or-directory/
$path = $args[0]
$handleOutput = & handle -a $path

if ($handleOutput -match "no matching handles found") {
    Write-Host "Nothing to kill, exiting"
    exit
}

$pidList = New-Object System.Collections.ArrayList
$lines = $handleOutput -split "`n"
foreach($line in $lines) {
  # sample line:
  # chrome.exe         pid: 11392  type: File           5BC: C:\Windows\Fonts\timesbd.ttf
  # regex to get pid and process name: (.*)\b(?:.*)(?:pid: )(\d*)
  $matches = $null
  $line -match "(.*)\b(?:.*)(?:pid: )(\d*)" | Out-Null
  if (-not $matches) { continue }
  if ($matches.Count -eq 0) { continue }
  $pidName = $matches[1]
  $pidStr = $matches[2]
  if ($pidList -notcontains $pidStr) {
    Write-Host "Will kill process $pidStr $pidName"
    $pidList.Add($pidStr) | Out-Null
  }
}

foreach($pidStr in $pidList) {
    $pidInt = [int]::Parse($pidStr)
    Stop-Process -Id $pidInt -Force
    Write-Host "Killed process $pidInt"
}

Write-Host "Finished"