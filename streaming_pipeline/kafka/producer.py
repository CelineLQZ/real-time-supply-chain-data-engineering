"""
Kafka Producer - 快速模式
快速批量发送CSV数据到Kafka（不模拟流式延迟）
用于本地快速测试和数据导入
"""
import csv
import json
import sys
from kafka import KafkaProducer
from kafka.errors import KafkaError
from kafka_config import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_TOPIC,
    CSV_FILE_PATH,
    BATCH_SIZE
)


def create_producer():
    """创建Kafka Producer"""
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks='all',  # 等待所有副本确认
            retries=3,
            batch_size=32768,  # 增加批处理大小以提高吞吐量
            linger_ms=10  # 等待10ms以便批处理更多消息
        )
        print(f"✓ 成功连接到 Kafka: {KAFKA_BOOTSTRAP_SERVERS}")
        return producer
    except Exception as e:
        print(f"✗ 连接 Kafka 失败: {e}")
        sys.exit(1)


def read_csv_data(file_path):
    """读取CSV文件并返回生成器"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield row
    except FileNotFoundError:
        print(f"✗ CSV文件未找到: {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ 读取CSV失败: {e}")
        sys.exit(1)


def main():
    print("=" * 60)
    print("Kafka Producer - 快速模式 (无流式延迟)")
    print("=" * 60)
    
    # 创建 Producer
    producer = create_producer()
    
    # 读取并发送数据
    print(f"\n开始发送 CSV 数据...")
    print(f"CSV 文件: {CSV_FILE_PATH}")
    print(f"Topic: {KAFKA_TOPIC}")
    print(f"批处理大小: {BATCH_SIZE}\n")
    
    sent_count = 0
    batch_count = 0
    
    try:
        for row in read_csv_data(CSV_FILE_PATH):
            # 异步发送消息（不等待响应以加快速度）
            producer.send(
                KAFKA_TOPIC,
                value=row,
                key=row.get('Order Id', '').encode('utf-8') if row.get('Order Id') else None
            )
            sent_count += 1
            
            # 每批次显示进度并 flush
            if sent_count % BATCH_SIZE == 0:
                batch_count += 1
                producer.flush()
                print(f"✓ 已发送批次 {batch_count}: {sent_count} 条记录")
        
        # 发送所有剩余消息
        producer.flush()
        print(f"\n{'=' * 60}")
        print(f"✓ 发送完成！总计: {sent_count} 条记录")
        print(f"✓ Consumer 现在可以开始消费数据")
        print(f"{'=' * 60}")
        
    except KeyboardInterrupt:
        print(f"\n✗ 用户中断发送")
    except Exception as e:
        print(f"✗ 发送过程出错: {e}")
    finally:
        producer.close()
        print("Producer 已关闭")


if __name__ == '__main__':
    main()
