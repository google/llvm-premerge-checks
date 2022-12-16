export PROJECT_ID="pre-merge-checks"
terraform init -backend-config="bucket=terraform-state-${PROJECT_ID}" -backend-config="prefix=terraform/state"

terraform apply -var-file="variables.tfvars" --auto-approve