# Installation

Install helm (along with other tools in `local_setup.sh`).

Once per cluster:

`helm install arc  --namespace "arc-system" --create-namespace oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set-controller`

## Add new set of runners

Create runner set first time:

- copy 'values.yml` and updata parameters: APP ID, target node set, repo etc
- run

```
helm install <runner-set> --namespace <k8s-namespace> --create-namespace \
  --values=$(readlink -f <values.yml>)
  --set-file=githubConfigSecret.github_app_private_key=$(readlink -f <pem>) \
  oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set
```

After that update values.yml to use `githubConfigSecret: arc-runner-set-gha-rs-github-secret`.

## Update

Example command for linux set:

`helm upgrade arc-google-linux --namespace arc-linux-prod -f $(readlink -f ~/src/merge-checks/actions-runner-controller/values-llvm.yaml) oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set`
