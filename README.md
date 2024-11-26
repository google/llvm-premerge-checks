This repo is holding VM configurations for machine cluster and scripts to run pre-merge tests triggered by http://reviews.llvm.org.

As LLVM project has moved to Pull Requests and Phabricator no longer triggers builds, this repository will likely be gone.

[Pull request migration schedule](https://discourse.llvm.org/t/pull-request-migration-schedule/71595).

# Overview

Presentation by Louis Dione on LLVM devmtg 2021 https://youtu.be/B7gB6van7Bw

[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/B7gB6van7Bw/0.jpg)](https://www.youtube.com/watch?v=B7gB6van7Bw)

## Feedback

If you notice issues or have an idea on how to improve pre-merge checks, please
create a [new issue](https://github.com/google/llvm-premerge-checks/issues/new)
or give a :heart: to an existing one.

# Restarting Buildbots

Restarting the buildbots can be accomplished be deleting the pods running the
buildbots. Kubernetes will automatically recreate the pod, essentially
performing a restart.

To find the name of the buildbot pod, first make sure you are using the correct
cluster configuration with `kubectl` as the windows and linux builders are on
separate clusters.

Then, find the name of the buildbot pod:

```bash
kubectl get pods | grep buildbot
```

Once you have the name of the pod, you can run the following command:

```bash
kubectl delete pod <pod name from previous step>
```

This command might take a couple minutes to execute as kubernetes stops
the running processes/container. The new pod will then spin up and
everything will hopefully work after the restart.

# Contributing

We're happy to get help on improving the infrastructure and workflows!

Please check [contributing](docs/contributing.md).

# License

This project is licensed under the "Apache 2.0 with LLVM Exception" license. See
[LICENSE](LICENSE) for details.
