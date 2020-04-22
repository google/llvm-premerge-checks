FROM debian:testing

RUN echo 'intall build dependencies'; \
    echo "deb [trusted=yes] http://apt.llvm.org/buster/ llvm-toolchain-buster-10 main\n$(cat /etc/apt/sources.list)" > /etc/apt/sources.list ;\
    apt-get update ;\
    apt-get install -y --no-install-recommends \
        locales openssh-client\
        cmake ninja-build git ca-certificates clang lld ccache python3 build-essential gdb \
        clang-tidy clang-format \
        python3-psutil zip wget \
        openjdk-11-jdk \
        python3-pip python3-setuptools \
        swig python3-dev libedit-dev libncurses5-dev libxml2-dev liblzma-dev golang rsync jq; \
    apt-get clean; \
    echo 'configure locale'; \
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