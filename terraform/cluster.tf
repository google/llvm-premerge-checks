resource "google_service_account" "llvm_premerge_checks_sa" {
  account_id   = "llvm-premerge-checks-sa"
  display_name = "Service Account used with the gke cluster"
}

resource "google_container_cluster" "llvm_premerge_checks_cluster" {
  name = "llvm-premerge-checks-cluster"

  location = var.zone

  network    = google_compute_network.vpc_network.name
  subnetwork = google_compute_subnetwork.vpc_subnetwork.name

  #enable_autopilot = true
  initial_node_count = 1

  #TODO: redo
  # master_authorized_networks_config {
  #   cidr_blocks {
  #     cidr_block= "0.0.0.0/0"
  #     display_name = "everyone"
  #   }
  # }

  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = var.master-cidr #todo: var
  }
  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }
}

resource "google_container_node_pool" "linux_agents_nodepool" {
  name    = "linux-agents"
  cluster = google_container_cluster.llvm_premerge_checks_cluster.id

  node_config {
    machine_type = var.linux-agents-machine-type

    #todo: assign right permissions and use custom service account
    service_account = "1047329282069-compute@developer.gserviceaccount.com" #google_service_account.llvm_premerge_checks_sa.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }

  autoscaling {
    min_node_count = 0
    max_node_count = 6
  }
}

#todo recheck
data "google_client_config" "provider" {}

provider "kubernetes" {
  host  = "https://${google_container_cluster.llvm_premerge_checks_cluster.endpoint}"
  token = data.google_client_config.provider.access_token
  cluster_ca_certificate = base64decode(
    google_container_cluster.llvm_premerge_checks_cluster.master_auth[0].cluster_ca_certificate,
  )
}

resource "kubernetes_manifest" "buildkite_namespace" {
  manifest = yamldecode(templatefile("kubernetes/namespace.yaml", {}))
}

resource "kubernetes_manifest" "buildkite_agent_token_secret" {
  manifest   = yamldecode(templatefile("kubernetes/secret-buildkite-token.yaml", { buildkite-agent-token = var.buildkite-agent-token }))
  depends_on = [kubernetes_manifest.buildkite_namespace]
}

resource "kubernetes_manifest" "buildkite_api_token_readonly_secret" {
  manifest   = yamldecode(templatefile("kubernetes/secret-buildkite-token-readonly.yaml", { buildkite-api-token-readonly = var.buildkite-api-token-readonly }))
  depends_on = [kubernetes_manifest.buildkite_namespace]
}

resource "kubernetes_manifest" "buildkite_github_secret" {
  manifest   = yamldecode(templatefile("kubernetes/secret-github-ssh.yaml", { git-id-rsa = var.git-id-rsa, id-rsa-pub = var.id-rsa-pub, git-known-hosts = var.git-known-hosts }))
  depends_on = [kubernetes_manifest.buildkite_namespace]
}

resource "kubernetes_manifest" "buildkite_conduit_api_token_secret" {
  manifest   = yamldecode(templatefile("kubernetes/secret-conduit-token.yaml", { conduit-api-token = var.conduit-api-token }))
  depends_on = [kubernetes_manifest.buildkite_namespace]
}

resource "kubernetes_manifest" "buildkite_linux_agent" {
  manifest   = yamldecode(templatefile("kubernetes/linux-agents.yaml", { project-id = var.project-id, gke-nodepool = google_container_node_pool.linux_agents_nodepool.name, build-queue = var.linux-agents-build-queue, cpu-request = var.linux-agents-cpu-request, mem-request = var.linux-agents-mem-request, replicas-count = var.linux-agents-count }))
  depends_on = [kubernetes_manifest.buildkite_namespace]
}