# Overview
This folder contains files related to the machines running the build/test/checks
for the merge guards.

## Scripts
The scripts are written in bash (for Linux) and powershell (for Windows).

### build_deploy.(sh|ps1)
Build the docker and deploy it to the GCP registry. This is useful for deploying
it in the Kubernetes cluster.

`buildkite-linux` has a cloudbuild.yaml and can be build / deployed by running
`gcloud builds submit --config ./cloudbuild.yaml`.

Note that some of the images are stored at
us-central1-docker.pkg.dev/llvm-premerge-checks/docker/ and some at
gcr.io/llvm-premerge-checks/ . Prefer a former one if possible.