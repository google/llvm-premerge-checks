#todo fix billing alert creation
#todo do not create billing if option in variables is off

resource "google_billing_budget" "budget" {
  billing_account = data.google_project.current_project.billing_account
  display_name    = "budget"
  amount {
    specified_amount {
      currency_code = "USD"
      units         = var.billing-budget
    }
  }
  

  budget_filter {
    projects               = ["projects/${data.google_project.current_project.number}"]
    credit_types_treatment = "EXCLUDE_ALL_CREDITS"
    calendar_period        = "MONTH"
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

  #TODO add if not empty billing admins var. Else use default admins
  all_updates_rule {
    monitoring_notification_channels = [
      for k, v in google_monitoring_notification_channel.notification_channel : google_monitoring_notification_channel.notification_channel[k].id
    ]
    disable_default_iam_recipients = length(var.billing-admins) < 1 ? false : true
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