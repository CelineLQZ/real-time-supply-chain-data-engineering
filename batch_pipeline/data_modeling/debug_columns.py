"""
调试脚本：查看 GCS 原始数据的实际列名
"""
import pyspark
from pyspark.sql import SparkSession
from config import credentials_path, jar_file_path, input_path, GCP_PROJECT_ID

# Create Spark Session
spark = SparkSession.builder \
    .appName('debug-columns') \
    .config("spark.jars", jar_file_path) \
    .config("spark.hadoop.fs.AbstractFileSystem.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFS") \
    .config("spark.hadoop.fs.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem") \
    .config("spark.hadoop.google.cloud.auth.service.account.enable", "true") \
    .config("spark.hadoop.google.cloud.auth.service.account.json.keyfile", credentials_path) \
    .config("spark.hadoop.google.cloud.project.id", GCP_PROJECT_ID) \
    .getOrCreate()

# Load data from GCS
print(f'Loading data from {input_path}')
df = spark.read.parquet(input_path + '*')

print(f'\n📊 原始数据统计：')
print(f'   → 行数：{df.count()}')
print(f'   → 列数：{len(df.columns)}')

print(f'\n📋 所有列名（{len(df.columns)} 列）：')
for i, col in enumerate(df.columns, 1):
    print(f'   {i:2d}. "{col}"')

# 查找包含 "date" 或 "Date" 的列
date_cols = [col for col in df.columns if 'date' in col.lower()]
if date_cols:
    print(f'\n📅 包含 "date" 的列：')
    for col in date_cols:
        print(f'   - "{col}"')

# 查找包含 "order" 的列
order_cols = [col for col in df.columns if 'order' in col.lower()]
if order_cols:
    print(f'\n🎯 包含 "order" 的列：')
    for col in order_cols:
        print(f'   - "{col}"')

spark.stop()
