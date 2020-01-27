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

# Pull and start the Docker container for a Windows agent.
# To setup a Windows agent see docs/playbooks.md

$NAME="agent-windows-jenkins"
$IMAGE="gcr.io/llvm-premerge-checks/${NAME}"

docker pull ${IMAGE}
docker stop ${NAME}
docker rm ${NAME}
docker run `
    -v D:\:C:\ws `
    -v C:\credentials:C:\credentials `
    -e PARENT_HOSTNAME=$env:computername `
    --restart unless-stopped `
    --name ${NAME} `
    ${IMAGE}