ToDo:
Move secrets to gcp secrets
Add readme
[]Add dependencies for kubernetes https://github.com/hashicorp/terraform-provider-kubernetes/issues/1775
Cloud build for terraform
Check billing alerts
Push images to the cluster or to central location
[?]Wait for kubernetes plugin to finish apply

1st run (bootstrap)

Copy variables.tfvars from variables.tfvars_example
Insert project-id and billing-account
Insert secret values in the variables.tfvars file or insert values on runtime when using terraform apply

Initialise terraform
Comment out everything in backend.tf file to use local state
terraform init

Create the state bucket
terraform apply -var-file=variables.tfvars -target="google_storage_bucket.terraform_state"
To disable the conformation use --auto-aprove flag

Move the state to the bucket
Uncomment everything in backend.tf file to use remote state
export PROJECT_ID="<PROJECT_ID>"
terraform init -backend-config="bucket=terraform-state-${PROJECT_ID}" -backend-config="prefix=terraform/state"

Create the cluster. Due to the problem described here [https://github.com/hashicorp/terraform-provider-kubernetes/issues/1775] kubernetes provider requires cluster to be created. So we have to do the apply in 2 runs using the -target flag
terraform apply -var-file=variables.tfvars -target="google_container_cluster.llvm_premerge_checks_cluster"

To deploy build slaves you need to have slaves docker images in your project. (TODO or we'll move them to the central project)

Create the rest of the resources
terraform apply -var-file="variables.tfvars"