FROM debian:testing

RUN apt-get update ;\
    apt-get install -y --no-install-recommends locales \
        cmake ninja-build git ca-certificates clang lld ccache python3 build-essential \
        clang-tidy clang-format \
        python3-psutil zip wget \
        openjdk-11-jdk \
        python3-pip python3-setuptools \
        swig python3-dev libedit-dev libncurses5-dev libxml2-dev liblzma-dev golang rsync jq; \
        apt-get clean

# Make python3 default (needed by git-clang-format and others).
RUN rm -f /usr/bin/python && ln -s /usr/bin/python3 /usr/bin/python
# required for openssh server
RUN mkdir -p /run/sshd

ARG user=buildkite
ARG group=buildkite
ARG uid=1000
ARG gid=1000
ARG AGENT_WORKDIR=/home/${user}/agent

RUN mkdir -p /scripts

COPY start_agent.sh /scripts/

# install python dependencies for the scripts
RUN pip3 install -r https://raw.githubusercontent.com/google/llvm-premerge-checks/master/scripts/phabtalk/requirements.txt

RUN groupadd -g ${gid} ${group} ;\
    useradd -c "buildkite user" -d /home/${user} -u ${uid} -g ${gid} -m ${user} ;\
    mkdir /home/${user}/ccache

RUN chown -R ${user}:${user} /home/${user}

WORKDIR /home/${user}
ENV CCACHE_PATH=/mnt/disks/ssd0/ccache

# configure locale
RUN sed --in-place '/en_US.UTF-8/s/^#//' /etc/locale.gen ;\
    locale-gen
ENV LANG en_US.UTF-8  
ENV LANGUAGE en_US:en  
ENV LC_ALL en_US.UTF-8  

# buildkite
RUN apt-get install -y apt-transport-https gnupg;\
    sh -c 'echo deb https://apt.buildkite.com/buildkite-agent stable main > /etc/apt/sources.list.d/buildkite-agent.list' ;\
    apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 32A37959C2FA5C3C99EFBC32A79206696452D198 ;\
    apt-get update ;\
    apt-get install -y buildkite-agent

VOLUME /credentials

CMD ["/scripts/start_agent.sh"]

