FROM debian:testing

RUN apt-get update ;\
    apt-get install -y --no-install-recommends \
        cmake ninja-build git ca-certificates clang-8 lld-8 ccache python python3 build-essential \
        clang-tidy-8 clang-format-8 \
        python-psutil arcanist zip \
        openjdk-11-jdk \
        openssh-server ;\
        apt-get clean

# required for openssh server
RUN mkdir -p /run/sshd

ARG user=jenkins
ARG group=jenkins
ARG uid=1000
ARG gid=1000
ARG AGENT_WORKDIR=/home/${user}/agent

RUN mkdir -p /scripts
COPY start_agent.sh report_results.sh /scripts/

# TODO(kuhnel): move ccache to SDD
RUN groupadd -g ${gid} ${group} ;\
    useradd -c "Jenkins user" -d /home/${user} -u ${uid} -g ${gid} -m ${user} ;\
    mkdir /home/${user}/ccache

COPY authorized_keys /home/${user}/.ssh/

RUN chown -R ${user}:${user} /home/${user} ;\
    chmod 700 /home/${user}/.ssh

WORKDIR /home/${user}
ENV CC=clang-8
ENV CXX=clang++-8

EXPOSE 22
CMD ["/scripts/start_agent.sh"]

