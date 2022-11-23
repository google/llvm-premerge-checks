#todo automatically rebuild buildkite images

resource "google_project_service" "cloudbuild_api" {
  service = "cloudbuild.googleapis.com"
}

resource "google_storage_bucket" "terraform_state" {
  name     = "terraform-state-${var.project-id}" #todo var
  location = "EU"
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
    asn = 64514
  }
}

resource "google_compute_router_nat" "nat" {
  name                               = "router-nat"
  router                             = google_compute_router.router.name
  region                             = google_compute_router.router.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
}
