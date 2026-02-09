"""
使用 Pandas 查看 GCS 中的数据 - 各显示 5 行
"""
import pandas as pd
from google.cloud import storage
from google.oauth2 import service_account
import io

# GCP 配置
credentials_path = '/Users/liceline/Documents/study_material/data_engineer/project_study/supply_chain/supply_chain_de_study/keys/gcp-cred.json'
bucket_name = 'supply-chain-data-bucket-485314'

# 初始化 GCS 客户端
credentials = service_account.Credentials.from_service_account_file(credentials_path)
storage_client = storage.Client(credentials=credentials)
bucket = storage_client.bucket(bucket_name)

print("=" * 80)
print("📊 使用 Pandas 查看 GCS 中的数据")
print("=" * 80)

# ============================================================================
# 1. 查看 raw_streaming 文件夹下的数据
# ============================================================================
print("\n📂 1. RAW_STREAMING 文件夹 (原始 Kafka 数据)")
print("-" * 80)

try:
    # 列出 raw_streaming 下的文件
    blobs = list(bucket.list_blobs(prefix='raw_streaming/'))
    parquet_files = [b for b in blobs if b.name.endswith('.parquet')]
    
    if parquet_files:
        # 取第一个文件
        first_file = parquet_files[0]
        print(f"✓ 读取文件：{first_file.name}")
        
        # 下载文件到内存
        file_content = first_file.download_as_bytes()
        df_raw = pd.read_parquet(io.BytesIO(file_content))
        
        print(f"  → 行数：{len(df_raw)}")
        print(f"  → 列数：{len(df_raw.columns)}")
        print(f"\n列名列表：")
        for i, col in enumerate(df_raw.columns, 1):
            print(f"   {i:2d}. {col}")
        
        print(f"\n前 5 行数据：")
        print(df_raw.head(5).to_string())
    else:
        print("✗ 没有找到 parquet 文件")
except Exception as e:
    print(f"✗ 错误：{str(e)}")

# ============================================================================
# 2. 查看 transformed_data/order_fact 文件夹下的数据
# ============================================================================
print("\n\n📂 2. TRANSFORMED_DATA/ORDER_FACT 文件夹")
print("-" * 80)

try:
    # 列出 transformed_data/order_fact 下的文件
    blobs = list(bucket.list_blobs(prefix='transformed_data/order_fact/'))
    parquet_files = [b for b in blobs if b.name.endswith('.parquet')]
    
    if parquet_files:
        # 取第一个文件
        first_file = parquet_files[0]
        print(f"✓ 读取文件：{first_file.name}")
        
        # 下载文件到内存
        file_content = first_file.download_as_bytes()
        df_order = pd.read_parquet(io.BytesIO(file_content))
        
        print(f"  → 行数：{len(df_order)}")
        print(f"  → 列数：{len(df_order.columns)}")
        print(f"\n列名列表：")
        for i, col in enumerate(df_order.columns, 1):
            print(f"   {i:2d}. {col}")
        
        # 检查是否有 Order_Date 列
        if 'Order_Date' in df_order.columns:
            print(f"\n✅ 找到 Order_Date 列！")
        else:
            print(f"\n❌ 没有找到 Order_Date 列")
        
        print(f"\n前 5 行数据：")
        print(df_order.head(5).to_string())
    else:
        print("✗ 没有找到 parquet 文件")
except Exception as e:
    print(f"✗ 错误：{str(e)}")

# ============================================================================
# 3. 查看 transformed_data/customer_dimension 文件夹下的数据
# ============================================================================
print("\n\n📂 3. TRANSFORMED_DATA/CUSTOMER_DIMENSION 文件夹")
print("-" * 80)

try:
    # 列出 transformed_data/customer_dimension 下的文件
    blobs = list(bucket.list_blobs(prefix='transformed_data/customer_dimension/'))
    parquet_files = [b for b in blobs if b.name.endswith('.parquet')]
    
    if parquet_files:
        # 取第一个文件
        first_file = parquet_files[0]
        print(f"✓ 读取文件：{first_file.name}")
        
        # 下载文件到内存
        file_content = first_file.download_as_bytes()
        df_customer = pd.read_parquet(io.BytesIO(file_content))
        
        print(f"  → 行数：{len(df_customer)}")
        print(f"  → 列数：{len(df_customer.columns)}")
        print(f"\n列名列表：")
        for i, col in enumerate(df_customer.columns, 1):
            print(f"   {i:2d}. {col}")
        
        print(f"\n前 5 行数据：")
        print(df_customer.head(5).to_string())
    else:
        print("✗ 没有找到 parquet 文件")
except Exception as e:
    print(f"✗ 错误：{str(e)}")

print("\n" + "=" * 80)
