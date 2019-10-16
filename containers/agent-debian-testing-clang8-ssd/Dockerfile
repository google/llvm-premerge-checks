FROM debian:testing

RUN apt-get update ;\
    apt-get install -y --no-install-recommends \
        cmake ninja-build git ca-certificates clang-8 lld-8 clang ccache python python3 build-essential \
        clang-tidy-8 clang-format-8 \
        python-psutil arcanist zip wget \
        openjdk-11-jdk \
        python3-pip python3-setuptools ;\
        apt-get clean

# required for openssh server
RUN mkdir -p /run/sshd

ARG user=jenkins
ARG group=jenkins
ARG uid=1000
ARG gid=1000
ARG AGENT_WORKDIR=/home/${user}/agent

RUN mkdir -p /scripts

# install the swarm client
RUN cd /scripts ;\
    wget https://repo.jenkins-ci.org/releases/org/jenkins-ci/plugins/swarm-client/3.17/swarm-client-3.17.jar ;\
    mv swarm-client-3.17.jar swarm-client.jar 

COPY start_agent.sh report_results.sh /scripts/

# for the phabtalk script
RUN pip3 install -r https://raw.githubusercontent.com/google/llvm-premerge-checks/master/scripts/phabtalk/requirements.txt

RUN groupadd -g ${gid} ${group} ;\
    useradd -c "Jenkins user" -d /home/${user} -u ${uid} -g ${gid} -m ${user} ;\
    mkdir /home/${user}/ccache

RUN chown -R ${user}:${user} /home/${user}

WORKDIR /home/${user}
ENV CCACHE_PATH=/mnt/disks/ssd0/ccache

CMD ["/scripts/start_agent.sh"]

