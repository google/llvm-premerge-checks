# Permissions
TODO

# Step 1: Bootstrap

Copy `variables.tfvars` from `variables.tfvars_example`
Replace the placeholders for `project-id` and `billing-account` in `variables.tfvars`
Insert secret values in the `variables.tfvars` file or insert values on runtime when using terraform plan or apply

### Initialise terraform with local backend
Comment out everything in `backend.tf` file to use local state for the first run as the bucket for storing the state is not created.
```
terraform -chdir=terraform init
```

### Create the state bucket
```
terraform -chdir=terraform apply -var-file=variables.tfvars -target="google_storage_bucket.terraform_state"
```
To disable the conformation use `--auto-aprove` flag

## Migrate the state to the bucket.
Uncomment everything in `backend.tf` file to use remote state with newly created bucket.
```
export PROJECT_ID="<PROJECT_ID>"
```
```
terraform -chdir=terraform init -backend-config="bucket=terraform-state-${PROJECT_ID}" -backend-config="prefix=terraform/state"
```
## Create the secrets.
```
terraform -chdir=terraform apply -var-file=variables.tfvars -target="google_secret_manager_secret.secret"
```

## Create the cluster. 
Due to the problem described [here](https://github.com/hashicorp/terraform-provider-kubernetes/issues/1775) terraform kubernetes provider requires kubernetes cluster to be created first. So to create the cluster without applying kubernetes resources we will do the apply in 2 runs using the `-target` flag.
```
terraform -chdir=terraform apply -var-file=variables.tfvars -target="google_container_cluster.llvm_premerge_checks_cluster"
```

## Build the builders
To deploy build workers you need the worker docker images in your project.
TODO cloud build SA permissions

### Linux worker image
Execute cloud build to build Linux worker:
```
gcloud builds submit --config=containers/buildkite-premerge-debian/cloudbuild.yaml containers/buildkite-premerge-debian/ --project=${PROJECT_ID}
```

### Windows worker image
Build windows cloud builder. Follow the steps described here: [link](https://github.com/GoogleCloudPlatform/cloud-builders-community/tree/master/windows-builder)

Execute cloud build to build Windows worker:
```
gcloud builds submit --config=containers/buildkite-premerge-windows/cloudbuild.yaml containers/buildkite-premerge-windows/ --project=${PROJECT_ID}
```

## Create the rest of the gcp resources including workers in kubernetes pods
```
terraform -chdir=terraform apply -var-file="variables.tfvars"
```

## Terraform cloud build automation
Manual trigger
```
gcloud builds submit --config=terraform/cloudbuild.yaml terraform --project=${PROJECT_ID} --substitutions=_GIT_REPO=${GIT_REPO}
```

Automatic trigger:
```
<TODO>
```

# Budget
Budget alerts set on the monthly basis. Notification emails will be triggered on 50%, 90% and 100% of you budget.

## Actions to reduce project costs
Adjust the GKE cluster nodes: Set the node count to 1 per built platform (Linux and Windows). The node count can be controlled from the `variables.tfvars` file using the `linux-agents-count` and `windows-agents-count` parameters. If these parameters are not set in the `variables.tfvars` file, you can check the default parameters configured in the `variables.tf` file.

## Break glass procedure
Regarding the break glass procedure for emergency configuration of the Kubernetes build nodes, you can use the following set of gcloud commands. It is recommended to execute them from the  [Cloud Shell](https://cloud.google.com/shell/docs/using-cloud-shell) for simplicity. Please note that these commands assume you have the necessary permissions and authentication to access and modify the GKE cluster.
```
export PROJECT_ID=<your project id>
export ZONE="europe-west3-c"

gcloud container clusters get-credentials ${PROJECT_ID}-cluster --zone ${ZONE} --project ${PROJECT_ID}
#gcloud container clusters update llvm-premerge-checks-cluster --node-pool linux-agents --zone ${ZONE} --project ${PROJECT_ID} --no-enable-autoscaling
gcloud container clusters resize llvm-premerge-checks-cluster --node-pool linux-agents --num-nodes 1 --zone ${ZONE} --project ${PROJECT_ID}
#gcloud container clusters update llvm-premerge-checks-cluster --node-pool windows-agents --zone ${ZONE} --project ${PROJECT_ID} --no-enable-autoscaling
gcloud container clusters resize llvm-premerge-checks-cluster --node-pool windows-agents --num-nodes 1 --zone ${ZONE} --project ${PROJECT_ID}
```

These commands will scale down the deployments to have a single replica for both the Linux and Windows agents. Adjust the replica count as needed. Please note that making changes to your GKE cluster configuration or scaling down nodes may impact the availability and performance of the pipeline. 