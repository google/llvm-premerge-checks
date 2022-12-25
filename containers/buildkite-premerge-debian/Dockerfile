FROM debian:stable

RUN echo 'intall packages'; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        locales openssh-client gnupg ca-certificates  \
        zip wget git \
        cmake gdb build-essential  \
        ninja-build \
        libelf-dev libffi-dev gcc-multilib \
# for llvm-libc tests that build mpfr and gmp from source
        autoconf automake libtool \
        ccache \
        python3 python3-psutil \
        python3-pip python3-setuptools \
        lsb-release software-properties-common \
        swig python3-dev libedit-dev libncurses5-dev libxml2-dev liblzma-dev golang rsync jq;

# LLVM must be installed after prerequsite packages.
ENV LLVM_VERSION=15
RUN echo 'install llvm ${LLVM_VERSION}'; \
    wget https://apt.llvm.org/llvm.sh; \
    chmod +x llvm.sh; \
    ./llvm.sh ${LLVM_VERSION};\
    apt-get update; \
    apt install -y clang-${LLVM_VERSION} clang-format-${LLVM_VERSION} clang-tidy-${LLVM_VERSION} lld-${LLVM_VERSION}; \
    ln -s /usr/bin/clang-${LLVM_VERSION} /usr/bin/clang;\
    ln -s /usr/bin/clang++-${LLVM_VERSION} /usr/bin/clang++;\
    ln -s /usr/bin/clang-tidy-${LLVM_VERSION} /usr/bin/clang-tidy;\
    ln -s /usr/bin/clang-tidy-diff-${LLVM_VERSION}.py /usr/bin/clang-tidy-diff;\
    ln -s /usr/bin/clang-format-${LLVM_VERSION} /usr/bin/clang-format;\
    ln -s /usr/bin/clang-format-diff-${LLVM_VERSION} /usr/bin/clang-format-diff;\
    ln -s /usr/bin/lld-${LLVM_VERSION} /usr/bin/lld;\
    ln -s /usr/bin/ld.lld-${LLVM_VERSION} /usr/bin/ld.lld

RUN echo 'configure locale'; \
    sed --in-place '/en_US.UTF-8/s/^#//' /etc/locale.gen ;\
    locale-gen ;\
    echo 'make python 3 default'; \
    rm -f /usr/bin/python && ln -s /usr/bin/python3 /usr/bin/python; \
    pip3 install wheel

# Configure locale
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

RUN echo 'install buildkite' ;\
    apt-get install -y apt-transport-https gnupg;\
    sh -c 'echo deb https://apt.buildkite.com/buildkite-agent stable main > /etc/apt/sources.list.d/buildkite-agent.list' ;\
    apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 32A37959C2FA5C3C99EFBC32A79206696452D198 ;\
    apt-get update ;\
    apt-get install -y buildkite-agent tini gosu; \
    apt-get clean;
COPY *.sh /usr/local/bin/
RUN chmod og+rx /usr/local/bin/*.sh
COPY --chown=buildkite-agent:buildkite-agent pre-checkout /etc/buildkite-agent/hooks
COPY --chown=buildkite-agent:buildkite-agent post-checkout /etc/buildkite-agent/hooks

# buildkite working directory
VOLUME /var/lib/buildkite-agent

ENTRYPOINT ["entrypoint.sh"]
CMD ["gosu", "buildkite-agent", "buildkite-agent", "start", "--no-color"]
