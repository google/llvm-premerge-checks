FROM ubuntu:latest

RUN echo 'intall packages'; \
    apt-get update; \
    apt-get upgrade; \
    apt-get install -y --no-install-recommends \
        gosu \
        locales openssh-client gnupg ca-certificates  \
        zip wget curl git \
        gdb build-essential  \
        ninja-build \
        libelf-dev libffi-dev gcc-multilib libmpfr-dev libpfm4-dev \
        # for llvm-libc tests that build mpfr and gmp from source
        autoconf automake libtool \
        python3 python3-psutil python3-pip python3-setuptools \
        lsb-release software-properties-common \
        swig python3-dev libedit-dev libncurses5-dev libxml2-dev liblzma-dev golang rsync jq \
        # for llvm installation script
        sudo \
        # build scripts
        nodejs \
	# shell users
	less vim

# debian stable cmake is 3.18, we need to install a more recent version.
RUN wget --no-verbose -O /cmake.sh https://github.com/Kitware/CMake/releases/download/v3.23.3/cmake-3.23.3-linux-x86_64.sh; \
    chmod +x /cmake.sh; \
    mkdir -p /etc/cmake; \
    /cmake.sh --prefix=/etc/cmake --skip-license; \
    ln -s /etc/cmake/bin/cmake /usr/bin/cmake; \
    cmake --version; \
    rm /cmake.sh

# LLVM must be installed after prerequsite packages.
ENV LLVM_VERSION=16
RUN echo 'install llvm ${LLVM_VERSION}' && \
    wget --no-verbose https://apt.llvm.org/llvm.sh && \
    chmod +x llvm.sh && \
    ./llvm.sh ${LLVM_VERSION} && \
    apt-get update && \
    apt-get install -y clang-${LLVM_VERSION} clang-format-${LLVM_VERSION} clang-tidy-${LLVM_VERSION} lld-${LLVM_VERSION} && \
    ln -s /usr/bin/clang-${LLVM_VERSION} /usr/bin/clang && \
    ln -s /usr/bin/clang++-${LLVM_VERSION} /usr/bin/clang++ && \
    ln -s /usr/bin/clang-tidy-${LLVM_VERSION} /usr/bin/clang-tidy && \
    ln -s /usr/bin/clang-tidy-diff-${LLVM_VERSION}.py /usr/bin/clang-tidy-diff && \
    ln -s /usr/bin/clang-format-${LLVM_VERSION} /usr/bin/clang-format && \
    ln -s /usr/bin/clang-format-diff-${LLVM_VERSION} /usr/bin/clang-format-diff && \
    ln -s /usr/bin/lld-${LLVM_VERSION} /usr/bin/lld && \
    ln -s /usr/bin/lldb-${LLVM_VERSION} /usr/bin/lldb && \
    ln -s /usr/bin/ld.lld-${LLVM_VERSION} /usr/bin/ld.lld && \
    clang --version

RUN echo 'configure locale' && \
    sed --in-place '/en_US.UTF-8/s/^#//' /etc/locale.gen && \
    locale-gen
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

RUN curl -o sccache-v0.5.4-x86_64-unknown-linux-musl.tar.gz -L https://github.com/mozilla/sccache/releases/download/v0.5.4/sccache-v0.5.4-x86_64-unknown-linux-musl.tar.gz \
    && echo "4bf3ce366aa02599019093584a5cbad4df783f8d6e3610548c2044daa595d40b  sccache-v0.5.4-x86_64-unknown-linux-musl.tar.gz" | shasum -a 256 -c \
    && tar xzf ./sccache-v0.5.4-x86_64-unknown-linux-musl.tar.gz \
    && mv sccache-v0.5.4-x86_64-unknown-linux-musl/sccache /usr/bin \
    && chown root:root /usr/bin/sccache \
    && ls -la /usr/bin/sccache \
    && sccache --version

WORKDIR /actions-runner

RUN cd /actions-runner \
    && curl -o actions-runner-linux-x64-2.308.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.308.0/actions-runner-linux-x64-2.308.0.tar.gz \
    && echo "9f994158d49c5af39f57a65bf1438cbae4968aec1e4fec132dd7992ad57c74fa  actions-runner-linux-x64-2.308.0.tar.gz" | shasum -a 256 -c \
    && tar xzf ./actions-runner-linux-x64-2.308.0.tar.gz

RUN groupadd -g 121 runner \
    && useradd -mr -d /home/runner -u 1001 -g 121 runner \
    && mkdir -p /_work \
    && chown -R runner:runner /_work /actions-runner;

COPY entrypoint.sh /
RUN chmod +x /entrypoint.sh
# try: USER runner instead of gosu
ENTRYPOINT ["/entrypoint.sh"]

CMD ["./bin/Runner.Listener", "run", "--startuptype", "service"]
