# #todo fix billing alert creation
# data "google_billing_account" "account" {
#   billing_account = "01E34D-BF37C6-8137F6"
# }

# resource "google_billing_budget" "budget" {
#   billing_account = data.google_billing_account.account.id
#   display_name = "budget"
#   amount {
#     specified_amount {
#       currency_code = "USD"
#       units = "25000"
#     }
#   }

#   budget_filter {
#     #projects = ["projects/${data.google_project.project.number}"]
#     credit_types_treatment = "EXCLUDE_ALL_CREDITS"
#     #services = ["services/24E6-581D-38E5"] # Bigquery
#   }

#   threshold_rules {
#     threshold_percent = 0.5
#   }
#   threshold_rules {
#     threshold_percent = 0.9
#   }
#   threshold_rules {
#     threshold_percent = 1.0
#   }

#   # all_updates_rule {
#   #   monitoring_notification_channels = [
#   #     google_monitoring_notification_channel.notification_channel.id,
#   #   ]
#   #   disable_default_iam_recipients = true
#   # }
# }

# resource "google_monitoring_notification_channel" "notification_channel" {
#   display_name = "Example Notification Channel"
#   type         = "email"

#   labels = {
#     email_address = "address@example.com"
#   }
# }