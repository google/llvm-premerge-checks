locals {
    secrets = {
        "buildkite-api-token-readonly": var.buildkite-api-token-readonly, 
        "buildkite-agent-token": var.buildkite-agent-token, 
        "conduit-api-token": var.conduit-api-token, 
        "git-id-rsa": var.git-id-rsa, 
        "id-rsa-pub": var.id-rsa-pub, 
        "git-known-hosts": var.git-known-hosts
    }
}

resource "google_secret_manager_secret" "secret" {
  for_each = local.secrets
  secret_id = each.key

  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "secret_version" {
  for_each = local.secrets
  secret = google_secret_manager_secret.secret[each.key].id

  secret_data = each.value
}