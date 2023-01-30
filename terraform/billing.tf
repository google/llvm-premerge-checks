#todo fix billing alert creation
data "google_billing_account" "account" {
  billing_account = var.billing-account
}

resource "google_billing_budget" "budget" {
  billing_account = data.google_billing_account.account.id
  display_name    = "budget"
  amount {
    specified_amount {
      currency_code = "USD"
      units         = var.billing-budget
    }
  }

  budget_filter {
    projects               = ["projects/${var.project-id}"]
    credit_types_treatment = "EXCLUDE_ALL_CREDITS"
    #services = ["services/24E6-581D-38E5"] # Bigquery
  }

  threshold_rules {
    threshold_percent = 0.5
  }
  threshold_rules {
    threshold_percent = 0.9
  }
  threshold_rules {
    threshold_percent = 1.0
  }

  all_updates_rule {
    monitoring_notification_channels = [
      for k, v in google_monitoring_notification_channel.notification_channel : google_monitoring_notification_channel.notification_channel[k].id
    ]
    disable_default_iam_recipients = true
  }
}

resource "google_monitoring_notification_channel" "notification_channel" {
  for_each     = var.billing-admins
  display_name = each.key
  type         = "email"

  labels = {
    email_address = each.value
  }
}