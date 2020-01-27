# Copyright 2019 Google LLC

# Licensed under the the Apache License v2.0 with LLVM Exceptions (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     https://llvm.org/LICENSE.txt

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# The script will benchmark the windows build steps.
# It can be used to optimize the build performance.

param(
    [Parameter(Mandatory=$true)][string]$WORKDIR
)

. ${PSScriptRoot}\common.ps1
function timeit() {
    param(
      [scriptblock] $cmd
    )
    Write-Host "Running $cmd..."
    $secs=Measure-Command @cmd | Select-Object -Property TotalSeconds
    if ($lastexitcode -ne 0) {
        Write-Error "$cmd failed!"
    }
    Write-Host "$cmd ran for $($secs.TotalSeconds)"
    #TODO: make this an absolute path!
    Add-Content benchmark.txt "$cmd : $($secs.TotalSeconds)"
}

Write-Host "Deleting work dir: $WORKDIR"
& cmd /c rd /s/q $WORKDIR | Out-Null
& cmd /c rd /s/q benchmark.txt | Out-Null
timeit {git clone --depth 1 https://github.com/llvm/llvm-project $WORKDIR}
Set-Location $WORKDIR
timeit {git pull}

timeit {& $PSScriptRoot\run_cmake.ps1}
timeit {& $PSScriptRoot\run_ninja.ps1 all}
timeit {& $PSScriptRoot\run_ninja.ps1 check-all}
# re-run to get time for tests without compilation
timeit {& $PSScriptRoot\run_ninja.ps1 check-all}
timeit {& cmd /c rd/s/q $WORKDIR}
