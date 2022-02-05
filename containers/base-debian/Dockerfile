# debian:unstable to get a go version > 1.11 (migth have other packages with different version, please check before updating)
FROM debian:unstable



RUN echo 'intall packages'; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        locales openssh-client gnupg ca-certificates  \
        zip wget git \
        cmake gdb build-essential  \
        ninja-build \
        libelf-dev libffi-dev gcc-multilib \
# for bolt subproject
        libc6-dev-i386 \
        ccache \
        python3 python3-psutil \
        python3-pip python3-setuptools \
        lsb-release software-properties-common \
        swig python3-dev libedit-dev libncurses5-dev libxml2-dev liblzma-dev golang rsync jq;

# LLVM must be installed after prerequsite packages.
RUN echo 'install llvm 13'; \
    wget https://apt.llvm.org/llvm.sh; \
    chmod +x llvm.sh; \
    ./llvm.sh 13;\
    apt-get update; \
    apt install -y clang-format-13 clang-tidy-13;

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

RUN ln -s /usr/bin/clang-13 /usr/bin/clang;\
    ln -s /usr/bin/clang++-13 /usr/bin/clang++;\
    ln -s /usr/bin/clang-tidy-13 /usr/bin/clang-tidy;\
    ln -s /usr/bin/clang-tidy-diff-13.py /usr/bin/clang-tidy-diff;\
    ln -s /usr/bin/clang-format-13 /usr/bin/clang-format;\
    ln -s /usr/bin/clang-format-diff-13 /usr/bin/clang-format-diff;\
    ln -s /usr/bin/lld-13 /usr/bin/lld;\
    ln -s /usr/bin/ld.lld-13 /usr/bin/ld.lld

