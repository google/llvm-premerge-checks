@rem Copyright 2019 Google LLC
@rem
@rem Licensed under the the Apache License v2.0 with LLVM Exceptions (the "License");
@rem you may not use this file except in compliance with the License.
@rem You may obtain a copy of the License at
@rem
@rem     https://llvm.org/LICENSE.txt
@rem
@rem Unless required by applicable law or agreed to in writing, software
@rem distributed under the License is distributed on an "AS IS" BASIS,
@rem WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
@rem See the License for the specific language governing permissions and
@rem limitations under the License.


set JENKINS_SERVER=jenkins.local
set AGENT_ROOT=C:\ws\

java -jar %SWARM_PLUGIN_JAR% -master http://%JENKINS_SERVER%:8080 -executors 1 -fsroot %AGENT_ROOT% -labels windows