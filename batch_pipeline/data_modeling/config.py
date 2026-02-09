"""
Batch Pipeline 数据建模配置文件
"""
import os
from pathlib import Path

# ===== 项目根目录 =====
PROJECT_ROOT = os.getenv('PROJECT_ROOT', '/Users/liceline/Documents/study_material/data_engineer/project_study/supply_chain/supply_chain_de_study')

# ===== GCP 项目信息 =====
GCP_PROJECT_ID = 'stellar-stream-485314-p0'
GCP_PROJECT_NAME = 'supply-chain-data-platform'
GCP_SERVICE_ACCOUNT = 'supply-chain-data-pipeline'
GCP_REGION = 'europe-west4'

# ===== GCP 认证 =====
credentials_path = os.path.join(PROJECT_ROOT, 'keys', 'gcp-cred.json')
gcp_credentials_path = credentials_path

# ===== BigQuery 配置 =====
BIGQUERY_DATASET = 'supply_chain_bigquery'
BIGQUERY_REGION = 'europe-west4'

# ===== Spark JAR 文件配置 =====
jar_file_path = os.path.join(PROJECT_ROOT, 'docker', 'spark', 'jar_files', 'gcs-connector-hadoop3-2.2.5.jar')

# ===== GCS 配置 =====
gcs_bucket_path = "gs://supply-chain-data-bucket-485314/"

# ===== 数据路径 =====
# 输入路径：来自流处理的原始数据（Parquet 格式）
input_path = gcs_bucket_path + "raw_streaming/"

# 转换后的数据输出路径
output_path = gcs_bucket_path + "transformed_data/"

# 数据建模层输出路径
modeled_data_path = gcs_bucket_path + "modeled_data/"

# ===== 本地数据源 =====
csv_file_path = os.path.join(PROJECT_ROOT, 'data', 'DataCoSupplyChainDataset.csv')

# ===== Spark 配置 =====
spark_app_name = 'supply-chain-batch-pipeline'
spark_master = 'local[*]'
spark_executor_memory = '4g'
spark_cores_max = 4
spark_shuffle_partitions = 200

# ===== 输出格式 =====
output_format = 'parquet'
compression = 'snappy'

# ===== 处理参数 =====
batch_size = 10000
partition_count = 4

# ===== 日志配置 =====
log_path = os.path.join(PROJECT_ROOT, 'logs', 'batch_pipeline')
Path(log_path).mkdir(parents=True, exist_ok=True)
