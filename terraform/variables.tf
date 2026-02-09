variable "credentials_file" {
  description = "Path to GCP service account JSON key file. Consider using file() in provider to load contents."
  type        = string
  default     = "../keys/gcp-cred.json"
}

variable "project_id" {
  description = "GCP project ID"
  type        = string
  default     = "stellar-stream-485314-p0"
}

variable "region" {
  description = "Default region for resources"
  type        = string
  default     = "europe-west4"
}

variable "bucket_name" {
  description = "Name of the GCS bucket"
  type        = string
  default     = "supply-chain-data-bucket-485314"
}

variable "bucket_location" {
  description = "Location/region for the GCS bucket"
  type        = string
  default     = "europe-west4"
}

variable "force_destroy" {
  description = "Allow Terraform to delete bucket and its objects"
  type        = bool
  default     = true
}

variable "public_access_prevention" {
  description = "Public access prevention setting: 'inherited' or 'enforced'"
  type        = string
  default     = "enforced"
  validation {
    condition     = contains(["inherited", "enforced"], var.public_access_prevention)
    error_message = "public_access_prevention must be 'inherited' or 'enforced'."
  }
}

variable "lifecycle_delete_age_days" {
  description = "Delete objects older than this number of days"
  type        = number
  default     = 30
}

variable "lifecycle_abort_multipart_age_days" {
  description = "Abort incomplete multipart uploads older than this number of days"
  type        = number
  default     = 10
}
