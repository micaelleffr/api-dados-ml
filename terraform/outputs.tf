output "cloud_run_url" {
  value = google_cloud_run_service.api.status[0].url
}

output "service_account_email" {
  value = google_service_account.ml_api_sa.email
}

output "dataset_id" {
  value = google_bigquery_dataset.ml_dataset.dataset_id
}

output "table_id" {
  value = google_bigquery_table.ml_table.table_id
}
