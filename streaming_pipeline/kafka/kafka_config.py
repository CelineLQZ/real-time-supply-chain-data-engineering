"""
Kafka 流处理配置文件
使用绝对路径，与文件结构无关
"""
import os
from pathlib import Path

# ===== 项目根目录 =====
# 使用绝对路径以避免相对路径问题
# 可通过环境变量 PROJECT_ROOT 覆盖
PROJECT_ROOT = os.getenv('PROJECT_ROOT', '/Users/liceline/Documents/study_material/data_engineer/project_study/supply_chain/supply_chain_de_study')

# ===== Kafka 配置 =====
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'supply-chain-orders')

# ===== GCS 配置 =====
GCS_BUCKET_NAME = os.getenv('GCS_BUCKET_NAME', 'supply-chain-data-bucket-485314')
GCS_CREDENTIALS_PATH = os.getenv('GCS_CREDENTIALS_PATH', os.path.join(PROJECT_ROOT, 'keys', 'gcp-cred.json'))
GCS_OUTPUT_PREFIX = os.getenv('GCS_OUTPUT_PREFIX', 'raw_streaming/')  # 修改为 raw_streaming/ 文件夹

# ===== 数据配置 =====
CSV_FILE_PATH = os.getenv('CSV_FILE_PATH', os.path.join(PROJECT_ROOT, 'data', 'DataCoSupplyChainDataset.csv'))
BATCH_SIZE = int(os.getenv('BATCH_SIZE', '1000'))  # 每批次发送的记录数
SEND_INTERVAL = int(os.getenv('SEND_INTERVAL', '1'))  # 发送间隔（秒，仅用于 producer.py）

# ===== Consumer 配置 =====
CONSUMER_GROUP_ID = os.getenv('CONSUMER_GROUP_ID', 'supply-chain-consumer-group')
AUTO_OFFSET_RESET = os.getenv('AUTO_OFFSET_RESET', 'earliest')  # 从最早的消息开始消费
