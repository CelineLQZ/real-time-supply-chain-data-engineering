"""
Kafka Consumer - 消费数据并写入 GCS
实时处理供应链订单数据
支持 JSON 和 Parquet 格式输出
"""
import json
import sys
import time
from datetime import datetime
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from google.cloud import storage
import os
import pandas as pd
from io import BytesIO

from kafka_config import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_TOPIC,
    CONSUMER_GROUP_ID,
    AUTO_OFFSET_RESET,
    GCS_BUCKET_NAME,
    GCS_CREDENTIALS_PATH,
    GCS_OUTPUT_PREFIX
)


class SupplyChainConsumer:
    """供应链数据消费者 - 高性能版本"""
    
    def __init__(self):
        self.consumer = None
        self.gcs_client = None
        self.bucket = None
        self.buffer = []
        self.buffer_size = 20000  # 增大缓冲区以减少 GCS 写入次数，生成更大的 Parquet 文件
        self.total_consumed = 0
        self.output_format = 'parquet'  # 默认输出 parquet 格式
        
    def setup_kafka_consumer(self):
        """初始化 Kafka Consumer - 高性能配置"""
        try:
            self.consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                group_id=CONSUMER_GROUP_ID,
                auto_offset_reset=AUTO_OFFSET_RESET,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                enable_auto_commit=True,
                auto_commit_interval_ms=5000,  # 减少提交频率提高性能
                max_poll_records=1000,  # 每次拉取更多消息
                fetch_min_bytes=1024,  # 最小拉取字节数
                fetch_max_bytes=52428800,  # 50MB - 增加单次拉取数据量
                fetch_max_wait_ms=500  # 最大等待时间
            )
            print(f"✓ 成功连接到 Kafka: {KAFKA_BOOTSTRAP_SERVERS}")
            print(f"✓ 订阅 Topic: {KAFKA_TOPIC}")
            print(f"✓ Consumer Group: {CONSUMER_GROUP_ID}\n")
            return True
        except Exception as e:
            print(f"✗ 连接 Kafka 失败: {e}")
            return False
    
    def setup_gcs_client(self):
        """初始化 GCS 客户端"""
        try:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = GCS_CREDENTIALS_PATH
            self.gcs_client = storage.Client()
            self.bucket = self.gcs_client.bucket(GCS_BUCKET_NAME)
            print(f"✓ 成功连接到 GCS Bucket: {GCS_BUCKET_NAME}\n")
            return True
        except Exception as e:
            print(f"✗ 连接 GCS 失败: {e}")
            print(f"  请确保:")
            print(f"  1. GCS_BUCKET_NAME 在 kafka_config.py 中正确配置")
            print(f"  2. keys/gcp-cred.json 文件存在且有效")
            print(f"  3. 服务账号有 Storage Object Creator 权限\n")
            return False
    
    def write_to_gcs(self, data, file_suffix=""):
        """写入数据到 GCS (支持 JSON 和 Parquet)"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if self.output_format == 'parquet':
                # 转换为 DataFrame 并写入 Parquet
                df = pd.DataFrame(data)
                filename = f"{GCS_OUTPUT_PREFIX}orders_{timestamp}{file_suffix}.parquet"
                
                # 使用 BytesIO 创建内存中的 Parquet 文件
                parquet_buffer = BytesIO()
                df.to_parquet(parquet_buffer, engine='pyarrow', index=False)
                parquet_buffer.seek(0)
                
                blob = self.bucket.blob(filename)
                blob.upload_from_string(
                    parquet_buffer.getvalue(),
                    content_type='application/octet-stream'
                )
                print(f"✓ 写入 GCS (Parquet): gs://{GCS_BUCKET_NAME}/{filename}")
                print(f"  ├─ 行数: {len(data)}")
                print(f"  ├─ 列数: {len(df.columns)}")
                print(f"  └─ 大小: {len(parquet_buffer.getvalue()) / 1024:.2f} KB")
            else:
                # 写入 JSON 格式
                filename = f"{GCS_OUTPUT_PREFIX}orders_{timestamp}{file_suffix}.json"
                blob = self.bucket.blob(filename)
                blob.upload_from_string(
                    json.dumps(data, indent=2, ensure_ascii=False),
                    content_type='application/json'
                )
                print(f"✓ 写入 GCS (JSON): gs://{GCS_BUCKET_NAME}/{filename} ({len(data)} 条记录)")
            
        except Exception as e:
            print(f"✗ 写入 GCS 失败: {e}")
            return False
    
    def flush_buffer(self):
        """刷新缓冲区到 GCS"""
        if self.buffer:
            success = self.write_to_gcs(self.buffer)
            if success:
                self.buffer = []
            return success
        return True
    
    def consume(self):
        """开始消费数据"""
        print("=" * 60)
        print("开始消费数据...")
        print(f"缓冲区大小: {self.buffer_size} 条记录")
        print(f"输出格式: {self.output_format.upper()}")
        print("=" * 60)
        print()
        
        try:
            for message in self.consumer:
                data = message.value
                self.buffer.append(data)
                self.total_consumed += 1
                
                # 显示进度（每 1000 条显示一次以减少 I/O）
                if self.total_consumed % 1000 == 0:
                    print(f"  已消费: {self.total_consumed} 条 | 缓冲区: {len(self.buffer)} 条")
                
                # 缓冲区满时写入 GCS
                if len(self.buffer) >= self.buffer_size:
                    self.flush_buffer()
                    
        except KeyboardInterrupt:
            print(f"\n\n✗ 用户中断")
        finally:
            # 写入剩余数据
            if self.buffer:
                print(f"\n正在写入剩余 {len(self.buffer)} 条记录...")
                self.flush_buffer()
            
            print(f"\n{'=' * 60}")
            print(f"✓ 消费完成！总计: {self.total_consumed} 条记录")
            print(f"{'=' * 60}")
            
            if self.consumer:
                self.consumer.close()
                print("Consumer 已关闭")


def main():
    print("=" * 60)
    print("Kafka Consumer - 供应链数据流处理")
    print("=" * 60)
    print()
    
    consumer_app = SupplyChainConsumer()
    
    # 初始化 Kafka
    if not consumer_app.setup_kafka_consumer():
        sys.exit(1)
    
    # 初始化 GCS
    if not consumer_app.setup_gcs_client():
        sys.exit(1)
    
    # 开始消费
    consumer_app.consume()


if __name__ == '__main__':
    main()
