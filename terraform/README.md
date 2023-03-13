#ToDo:
Move secrets to gcp secrets
Format readme in md
Cloud build for terraform
[?]Wait for kubernetes plugin to finish apply
Add readme if the budget is exceeded

Be aware, the actions you execute on your gcp project will generate some cost.

#Permissions
TODO

#1st run (bootstrap)

Copy `variables.tfvars` from `variables.tfvars_example`
Replace the placeholders for `project-id` and `billing-account` in `variables.tfvars`
Insert secret values in the `variables.tfvars` file or insert values on runtime when using terraform plan or apply

Initialise terraform
Comment out everything in `backend.tf` file to use local state for the first run as the bucket for storing the state is not created.
```terraform init```

Create the state bucket
```terraform apply -var-file=variables.tfvars -target="google_storage_bucket.terraform_state"```
To disable the conformation use `--auto-aprove` flag

##Move the state to the bucket.
Uncomment everything in `backend.tf` file to use remote state with newly created bucket.
```export PROJECT_ID="<PROJECT_ID>"```
```terraform init -backend-config="bucket=terraform-state-${PROJECT_ID}" -backend-config="prefix=terraform/state"```

Create the cluster. Due to the problem described [here](https://github.com/hashicorp/terraform-provider-kubernetes/issues/1775) terraform kubernetes provider requires kubernetes cluster to be created first. So to create the cluster without applying kubernetes resources we will do the apply in 2 runs using the `-target` flag.
```terraform apply -var-file=variables.tfvars -target="google_container_cluster.llvm_premerge_checks_cluster"```

##Creating worker images
To deploy build workers you need the worker docker images in your project.
TODO cloud build SA permissions

###Linux worker image
Execute cloud build to build Linux worker:
```gcloud builds submit --config=containers/buildkite-premerge-debian/cloudbuild.yaml containers/buildkite-premerge-debian/ --project=${PROJECT_ID}```

###Windows worker image
Build windows cloud builder. Follow the steps described here: [link](https://github.com/GoogleCloudPlatform/cloud-builders-community/tree/master/windows-builder)

Execute cloud build to build Windows worker:
```gcloud builds submit --config=containers/buildkite-premerge-windows/cloudbuild.yaml containers/buildkite-premerge-windows/ --project=${PROJECT_ID}```

##Create the rest of the gcp resources including workers in kubernetes pods
```terraform apply -var-file="variables.tfvars"```

#Budget
TODO