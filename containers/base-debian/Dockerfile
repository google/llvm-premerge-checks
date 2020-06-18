FROM debian:buster

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
        swig python3-dev libedit-dev libncurses5-dev libxml2-dev liblzma-dev golang rsync jq;
RUN wget -O - https://apt.llvm.org/llvm-snapshot.gpg.key | apt-key add - ;\
    echo "deb http://apt.llvm.org/buster/ llvm-toolchain-buster-10 main\ndeb-src http://apt.llvm.org/buster/ llvm-toolchain-buster-10 main\n$(cat /etc/apt/sources.list)" > /etc/apt/sources.list ;\
    cat /etc/apt/sources.list; \
    apt-get update ;\
    apt-get upgrade -y ;\
    apt-get install -y \
        clang-10 lld-10 clang-tidy-10 clang-format-10 \
        ;\
    ln -s /usr/bin/clang-10 /usr/bin/clang;\
    ln -s /usr/bin/clang++-10 /usr/bin/clang++;\
    ln -s /usr/bin/clang-tidy-10 /usr/bin/clang-tidy;\
    ln -s /usr/bin/clang-tidy-diff-10 /usr/bin/clang-tidy-diff;\
    ln -s /usr/bin/clang-format-10 /usr/bin/clang-format;\
    ln -s /usr/bin/clang-format-diff-10 /usr/bin/clang-format-diff;\
    ln -s /usr/bin/lld-10 /usr/bin/lld;\
    apt-get clean;

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

# Install python dependencies for the scripts. ADD will check contentents of a file for changes changed.
# TODO: that should be done during the build as it will pull this repo anyway and will have latest version.
ADD "https://raw.githubusercontent.com/google/llvm-premerge-checks/master/scripts/requirements.txt" requirements.txt
RUN pip3 install -r requirements.txt