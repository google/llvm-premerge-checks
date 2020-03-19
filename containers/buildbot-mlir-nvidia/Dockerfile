FROM nvidia/cuda:10.2-base

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

COPY test.sh /tests
CMD /tests/test.sh