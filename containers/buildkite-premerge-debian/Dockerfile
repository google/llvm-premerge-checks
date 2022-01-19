FROM gcr.io/llvm-premerge-checks/base-debian:latest

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