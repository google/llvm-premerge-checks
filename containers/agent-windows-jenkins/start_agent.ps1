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

$JENKINS_SERVER="jenkins.local"

$AGENT_ROOT="C:\ws"

# TODO(kuhnel): The autentication does not work!
# trying to copy the .boto file instead
# authenticate gsutil
# Write-Output "C:\credentials\build-agent-results_key.json`nllvm-premerge-checks`n`n" | gsutil config -e
Copy-Item "C:\credentials\.boto" "C:\Users\ContainerAdministrator\.boto"

$env:TEMP="${$AGENT_ROOT}\TEMP"
$env:TMP="${env:TEMP}"

# set local cache folder for sccache
$env:SCCACHE_DIR="C:\ws\sccache"
# Start sccache server and keep it running to avoid problems with Jenkins
# https://github.com/mozilla/sccache/blob/master/docs/Jenkins.md
$env:SCCACHE_IDLE_TIMEOUT="0"

# wipe cache at startup, otherwise it will time out
Remove-Item -Recurse -Force $env:SCCACHE_DIR
sccache --start-server
if ($lastexitcode -ne 0) {
    Write-Error "Failed to start sccache server."
    exit $lastexitcode
}

# start Jenkins agent
java -jar ${env:SWARM_PLUGIN_JAR} `
    -master http://${JENKINS_SERVER}:8080 `
    -executors 1 `
    -fsroot ${AGENT_ROOT} `
    -labels "windows vs2019 cores_${env:NUMBER_OF_PROCESSORS}" `
    -name ${env:PARENT_HOSTNAME} 