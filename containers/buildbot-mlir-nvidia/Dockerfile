# There is already an Ubuntu image with cuda :)
FROM nvidia/cuda:10.2-base

# for the host configuration see:
# https://github.com/NVIDIA/nvidia-docker

# install build tools
# set -eux;\
RUN apt-get update; \
    apt-get install -y cmake clang-8 lld-8 ninja-build python-psutil git wget gnupg;\
    update-alternatives --install /usr/bin/clang clang /usr/bin/clang-8 100 ;\
    update-alternatives --install /usr/bin/clang++ clang++ /usr/bin/clang++-8 100 ;\
    update-alternatives --install /usr/bin/lld lld /usr/bin/lld-8 100

# just for testing
RUN mkdir /tests ;\
    cd /tests ;\
    git clone --depth 1 https://github.com/llvm/llvm-project 

# install cuda
# avoid popups for keyboard configurations
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y cuda
RUN apt-get install -y python-virtualenv python-pip
# setup build bot
RUN mkdir /buildbot ;\
    cd /buildbot ;\
    mkdir buildmaster ;\   
    mkdir workspace ;\
    virtualenv -p python2 venv ;\
    . venv/bin/activate ;\
    pip install sqlalchemy-migrate==0.7.1 ;\
    # old version, dependencies seem broken!
    pip install --ignore-installed sqlalchemy-migrate buildbot==0.8.5 ;\
    pip install buildbot-slave==0.8.5

COPY test.sh /tests
VOLUME /buildbot/buildmaster
VOLUME /buildbot/workspace
CMD /buildbot/venv/bin/buildbot start /buildbot/workspace