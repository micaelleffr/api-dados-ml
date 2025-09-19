# Provedor GCP (conecta o terraform)
provider "google" {
  project = var.project
  region  = var.region
}

# Service Account
resource "google_service_account" "ml_api_sa" {
  account_id   = "ml-api-sa"
  display_name = "Service Account para Cloud Run API"
}

# Permissão do BigQuery p Service Account
resource "google_project_iam_member" "ml_api_sa_bigquery" {
  project = var.project
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.ml_api_sa.email}"
}

# Cria Dataset BigQuery
resource "google_bigquery_dataset" "ml_dataset" {
  dataset_id = var.dataset_id
  location   = "US"
}

# Cria Tabela BigQuery
resource "google_bigquery_table" "ml_table" {
  dataset_id = google_bigquery_dataset.ml_dataset.dataset_id
  table_id   = var.table_id
  schema     = <<EOF
[
  {
    "name": "id",
    "type": "INTEGER",
    "mode": "REQUIRED"
  },
  {
    "name": "nome",
    "type": "STRING",
    "mode": "REQUIRED"
  },
  {
    "name": "valor",
    "type": "FLOAT",
    "mode": "REQUIRED"
  }
]
EOF
}

# Cria API no Cloud Run
resource "google_cloud_run_service" "api" {
  name     = "ml-api"
  location = var.region

  template {
    spec {
      service_account_name = google_service_account.ml_api_sa.email

      containers {
        image = var.image
      }
    }
  }

  traffic {
    percent          = 100
    latest_revision  = true
  }
}
