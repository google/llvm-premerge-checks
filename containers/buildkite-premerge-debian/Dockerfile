FROM gcr.io/llvm-premerge-checks/base-debian:latest

RUN echo 'install buildkite' ;\
    apt-get install -y apt-transport-https gnupg;\
    sh -c 'echo deb https://apt.buildkite.com/buildkite-agent stable main > /etc/apt/sources.list.d/buildkite-agent.list' ;\
    apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 32A37959C2FA5C3C99EFBC32A79206696452D198 ;\
    apt-get update ;\
    apt-get install -y buildkite-agent tini gosu; \
    apt-get clean;
COPY *.sh /usr/local/bin/

# LLVM must be installed after prerequsite packages.
RUN echo 'install llvm 13'; \
    wget https://apt.llvm.org/llvm.sh; \
    chmod +x llvm.sh; \
    ./llvm.sh 13;\
    apt-get update; \
    apt install -y clang-format-13 clang-tidy-13;

RUN ln -s /usr/bin/clang-13 /usr/bin/clang;\
    ln -s /usr/bin/clang++-13 /usr/bin/clang++;\
    ln -s /usr/bin/clang-tidy-13 /usr/bin/clang-tidy;\
    ln -s /usr/bin/clang-tidy-diff-13.py /usr/bin/clang-tidy-diff;\
    ln -s /usr/bin/clang-format-13 /usr/bin/clang-format;\
    ln -s /usr/bin/clang-format-diff-13 /usr/bin/clang-format-diff;\
    ln -s /usr/bin/lld-13 /usr/bin/lld

RUN chmod og+rx /usr/local/bin/*.sh
COPY --chown=buildkite-agent:buildkite-agent pre-checkout /etc/buildkite-agent/hooks
COPY --chown=buildkite-agent:buildkite-agent post-checkout /etc/buildkite-agent/hooks

# buildkite working directory
VOLUME /var/lib/buildkite-agent

ENTRYPOINT ["entrypoint.sh"]
CMD ["gosu", "buildkite-agent", "buildkite-agent", "start", "--no-color"]
