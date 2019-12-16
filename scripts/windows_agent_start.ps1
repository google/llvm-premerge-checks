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


. ${PSScriptRoot}\common.ps1

$JENKINS_SERVER="jenkins.local"
$AGENT_ROOT="D:\"
$SWARM_PLUGIN_JAR="C:\jenkins\swarm-client.jar"

java -jar ${SWARM_PLUGIN_JAR} -master http://${JENKINS_SERVER}:8080 -executors 1 -fsroot ${AGENT_ROOT} -labels windows