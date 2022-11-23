terraform {
  backend "gcs" {
    #has to have the same name as the tf state bucket created in main.tf
    bucket = "terraform-state-pre-merge-checks" #todo var
    prefix = "terraform/state"
  }
}