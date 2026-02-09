"""Load transformed Parquet files from GCS into BigQuery tables.

Usage:
  python load_to_bigquery.py

Prerequisites:
  - GCP service account JSON at ./keys/gcp-cred.json
  - GCS bucket contains transformed_data/<dimension>/part-*.parquet
"""

import os
from google.cloud import bigquery
from google.oauth2 import service_account

from batch_pipeline.data_modeling.config import (
    BIGQUERY_DATASET,
    GCP_PROJECT_ID,
    credentials_path,
    gcs_bucket_path,
)


def normalize_bucket_name(bucket_path: str) -> str:
    if bucket_path.startswith("gs://"):
        return bucket_path.replace("gs://", "").rstrip("/")
    return bucket_path.rstrip("/")


def load_dimensions_to_bigquery(
    project_id: str,
    dataset_id: str,
    gcs_bucket: str,
    credentials_file: str,
) -> None:
    table_mapping = {
        "customer_dimension": "dim_customer",
        "product_dimension": "dim_product",
        "location_dimension": "dim_location",
        "order_fact": "fact_order",
        "shipping_dimension": "dim_shipping",
        "department_dimension": "dim_department",
        "metadata_dimension": "dim_metadata",
    }

    credentials = service_account.Credentials.from_service_account_file(credentials_file)
    client = bigquery.Client(project=project_id, credentials=credentials)

    for source_name, table_name in table_mapping.items():
        source_uri = f"gs://{gcs_bucket}/transformed_data/{source_name}/*"
        table_id = f"{project_id}.{dataset_id}.{table_name}"

        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.PARQUET,
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        )

        load_job = client.load_table_from_uri(
            source_uris=source_uri,
            destination=table_id,
            job_config=job_config,
        )
        load_job.result()
        print(f"Loaded {source_name} -> {table_id}")


def main() -> None:
    project_id = os.getenv("BQ_PROJECT_ID", GCP_PROJECT_ID)
    dataset_id = os.getenv("BQ_DATASET_ID", BIGQUERY_DATASET)
    gcs_bucket = os.getenv("GCS_BUCKET", normalize_bucket_name(gcs_bucket_path))
    credentials_file = os.getenv("GCP_CREDENTIALS", credentials_path)

    load_dimensions_to_bigquery(
        project_id=project_id,
        dataset_id=dataset_id,
        gcs_bucket=gcs_bucket,
        credentials_file=credentials_file,
    )


if __name__ == "__main__":
    main()
