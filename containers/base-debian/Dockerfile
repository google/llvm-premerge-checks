# debian:unstable to get a go version > 1.11 (migth have other packages with different version, please check before updating)
FROM debian:unstable

RUN echo 'intall build dependencies'; \
    apt-get update ;\
    apt-get install -y --no-install-recommends \
        locales openssh-client gnupg ca-certificates  \
        zip wget git \
        cmake gdb build-essential  \
        ninja-build \
        ccache \
        python3 python3-psutil \
        python3-pip python3-setuptools \
        lsb-release software-properties-common \
        swig python3-dev libedit-dev libncurses5-dev libxml2-dev liblzma-dev golang rsync jq;
RUN wget https://apt.llvm.org/llvm.sh; \
    chmod +x llvm.sh; \
    ./llvm.sh 12;\
    apt install -y clang-format-12 clang-tidy-12

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

RUN ln -s /usr/bin/clang-12 /usr/bin/clang;\
    ln -s /usr/bin/clang++-12 /usr/bin/clang++;\
    ln -s /usr/bin/clang-tidy-12 /usr/bin/clang-tidy;\
    ln -s /usr/bin/clang-tidy-diff-12.py /usr/bin/clang-tidy-diff;\
    ln -s /usr/bin/clang-format-12 /usr/bin/clang-format;\
    ln -s /usr/bin/clang-format-diff-12 /usr/bin/clang-format-diff;\
    ln -s /usr/bin/lld-12 /usr/bin/lld

