#todo automatically rebuild buildkite images

data "google_project" "current_project" {
  project_id = var.project-id
}

locals {
  cloud_build_sa_roles = ["roles/editor", "roles/storage.objectAdmin", "roles/secretmanager.secretAccessor","roles/secretmanager.viewer","roles/resourcemanager.projectIamAdmin"]
  enabled_apis = [
    "secretmanager.googleapis.com", 
    "billingbudgets.googleapis.com", 
    "cloudbuild.googleapis.com", 
    "compute.googleapis.com", 
    "container.googleapis.com", 
    "cloudresourcemanager.googleapis.com", 
    "cloudbilling.googleapis.com"
  ]
}

#todo create separate sa for cloud build
# data "google_iam_policy" "cloud_build_sa" {
#   binding {
#     role = "roles/iam.serviceAccountUser"

#     members = [
#       "serviceAccount:${data.google_project.current_project.number}-compute@developer.gserviceaccount.com",
#     ]
#   }
# }

# resource "google_service_account_iam_policy" "admin-account-iam" {
#   service_account_id = "${data.google_project.current_project.id}/serviceAccounts/${data.google_project.current_project.number}@cloudbuild.gserviceaccount.com"
#   policy_data        = data.google_iam_policy.cloud_build_sa.policy_data
# }

resource "google_project_iam_member" "cloudbuild_sa_roles" {
  project  = var.project-id
  for_each = toset(local.cloud_build_sa_roles)
  role     = each.value

  member = "serviceAccount:${data.google_project.current_project.number}@cloudbuild.gserviceaccount.com"
}

resource "google_project_service" "google_api" {
  for_each = toset(local.enabled_apis)
  service = each.value
}

resource "google_storage_bucket" "terraform_state" {
  name                        = "terraform-state-${var.project-id}"
  uniform_bucket_level_access = true
  location                    = "EU"
  depends_on = [google_project_service.google_api]
}

resource "google_compute_network" "vpc_network" {
  name                    = "vpc-network"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "vpc_subnetwork" {
  name          = "subnetwork"
  ip_cidr_range = var.subnetwork-main-cidr
  region        = var.region
  network       = google_compute_network.vpc_network.id
  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = var.subnetwork-pods-cidr
  }
  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = var.subnetwork-services-cidr
  }
}

resource "google_compute_router" "router" {
  name    = "router"
  region  = google_compute_subnetwork.vpc_subnetwork.region
  network = google_compute_network.vpc_network.id

  bgp {
    asn = 64514 #todo recheck
  }
}

resource "google_compute_router_nat" "nat" {
  name                               = "router-nat"
  router                             = google_compute_router.router.name
  region                             = google_compute_router.router.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
}
