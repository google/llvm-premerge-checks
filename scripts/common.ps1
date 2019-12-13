# Copyright 2019 Google LLC
#
# Licensed under the the Apache License v2.0 with LLVM Exceptions (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://llvm.org/LICENSE.txt
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# common header file for all .ps1 scripts

# stop script on errors
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$PSDefaultParameterValues['*:ErrorAction']='Stop'


# Invokes a Cmd.exe shell script and updates the environment.
# from: https://stackoverflow.com/questions/41399692/running-a-build-script-after-calling-vcvarsall-bat-from-powershell
function Invoke-CmdScript {
    param(
      [String] $scriptName
    )
    $cmdLine = """$scriptName"" $args & set"
    & $Env:SystemRoot\system32\cmd.exe /c $cmdLine |
    select-string '^([^=]*)=(.*)$' | foreach-object {
      $varName = $_.Matches[0].Groups[1].Value
      $varValue = $_.Matches[0].Groups[2].Value
      set-item Env:$varName $varValue
    }
  }


# call an executable and check the error code
# from: https://stackoverflow.com/questions/9948517/how-to-stop-a-powershell-script-on-the-first-error
function Invoke-Call {
    param (
        [scriptblock]$ScriptBlock,
        [string]$ErrorAction = $ErrorActionPreference
    )
    & @ScriptBlock 2>&1 | %{ "$_" }
    if (($lastexitcode -ne 0) -and $ErrorAction -eq "Stop") {
        Write-Error "Command $ScriptBlock exited with $lastexitcode."
        exit $lastexitcode
    }
}
