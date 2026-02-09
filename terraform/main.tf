terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
      version = "7.16.0"
    }
  }
}

provider "google" {
  credentials = file(var.credentials_file)
  project     = var.project_id
  region      = var.region
}

resource "google_storage_bucket" "supply_chain_data_bucket" {
  name                        = var.bucket_name
  location                    = var.bucket_location
  force_destroy               = var.force_destroy
  uniform_bucket_level_access = true
  public_access_prevention    = var.public_access_prevention

  lifecycle_rule {
    condition {
      age = var.lifecycle_delete_age_days
    }
    action {
      type = "Delete"
    }
  }

  lifecycle_rule {
    condition {
      age = var.lifecycle_abort_multipart_age_days
    }
    action {
      type = "AbortIncompleteMultipartUpload"
    }
  }
}

resource "google_bigquery_dataset" "supply_chain_dataset" {
  dataset_id = "supply_chain_bigquery_dataset"
  project    = var.project_id
  location   = var.region
}