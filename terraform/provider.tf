provider "google" {
  project               = var.project-id
  region                = var.region
  zone                  = var.zone
  billing_project       = var.project-id
  user_project_override = true
}