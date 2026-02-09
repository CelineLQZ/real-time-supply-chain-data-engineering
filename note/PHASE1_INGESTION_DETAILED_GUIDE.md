# 第一阶段：从零开始的数据获取（Ingestion）详细指南

> 假设你完全不懂，从零开始建立一个 Kafka + Streaming Producer + Mage Consumer 的数据摄入系统

---

### 📌 首先，理解整个流程

```
Kaggle 批量数据 (CSV)
    ↓
    ├─→ Kafka Producer (读取 CSV，逐行发送到 Kafka)
    │       ↓
    │   Kafka Topic: "supply_chain_data"
    │       ↓
    └─→ Mage Consumer (从 Kafka 消费数据，写入 GCS)
            ↓
        GCS Bucket: raw_streaming/*.parquet
```

## ❓ 问题一：原始数据应该保存在哪里？

### 答案：

**你应该把原始 CSV 文件存放在项目的本地目录中**

```
supply_chain_de_study/
├── data/                              # ← 原始数据放这里
│   ├── DataCoSupplyChainDataset.csv  
│   ├── DescriptionDataCoSupplyChain.csv
│   └── tokenized_access_logs.csv
├── producer.py                        # Kafka producer 脚本
├── consumer.py                        # Kafka consumer 脚本
├── config.py                          # 配置文件
├── docker-compose-kafka.yml           # Kafka Docker 配置
├── docker-compose-mage.yml            # Mage Docker 配置
└── docker-compose-postgres.yml        # PostgreSQL Docker 配置
```

### 为什么在本地？

- **开发阶段**：便于快速测试和调试
- **CSV 文件小**：供应链数据通常 < 1GB，可以本地存储
- **避免网络成本**：不需要频繁从云端下载
- **流程模拟**：模拟真实的流式数据来源（比如日志文件、数据库导出）

### 数据来源（Kaggle）

```bash
# 你应该从 Kaggle 下载数据：
# https://www.kaggle.com/datasets/shashwatwork/dataco-smart-supply-chain-for-big-data-analysis

# 然后把 CSV 放在 supply_chain_de_study/data/ 目录下
```

---

## ❓ 问题二：涉及 PostgreSQL 和 GCS 吗？

### 答案：**部分涉及**


| 组件           | 是否需要  | 作用                                         |
| ---------------- | ----------- | ---------------------------------------------- |
| **PostgreSQL** | ✅ 需要   | Mage 的元数据存储（pipeline 配置、执行历史） |
| **GCS**        | ✅ 需要   | 存储消费后的 parquet 文件                    |
| **GPS 坐标**   | ✅ 有数据 | CSV 中包含纬度/经度字段，但不特殊处理        |

### 详细说明：

#### PostgreSQL 的作用

```
Mage 需要一个数据库来存储：
├─ Pipeline 配置
├─ 执行日志
├─ 触发器信息
├─ 块（Blocks）的配置
└─ 消费者的偏移量（offset tracking）
```

**但是**：这是 Mage 的内部需求，你不需要手动操作它。Docker Compose 会自动启动。

#### GCS 的作用

```
Mage Consumer 将数据存储到 GCS：
gs://your-bucket-name/raw_streaming/*.parquet
    ↓
供给下一阶段（Spark Transform）使用
```

**但是**：如果你还没有 GCP 账户，你可以先**本地测试**，使用本地文件系统替代 GCS。

---

## ❓ 问题三：能用 Airflow 替代 Mage 吗？

### 答案：**理论上可以，但不推荐。原因如下：**


| 特性           | Mage             | Airflow         |
| ---------------- | ------------------ | ----------------- |
| **学习曲线**   | 🟢 陡峭          | 🔴 更陡         |
| **Kafka 集成** | 🟢 原生支持      | 🟡 需要插件     |
| **实时流处理** | 🟢 内置 Streamer | 🔴 不是设计目标 |
| **配置方式**   | 🟢 UI + YAML     | 🔴 只有 Python  |
| **启动速度**   | 🟢 快            | 🔴 慢           |
| **资源占用**   | 🟢 低 (~500MB)   | 🔴 高 (~2GB)    |

### Mage vs Airflow 的区别

**Mage 的设计**：

```python
# Mage 方式：编写一个数据管道，三个块（Blocks）
@loader                    # 1. 加载块 - 从 Kafka 读取
def load_from_kafka():
    # 消费 Kafka 数据
    pass

@transformer               # 2. 转换块 - 数据处理
def transform_data(data):
    # 清洗、转换
    pass

@exporter                  # 3. 导出块 - 写入 GCS
def export_to_gcs(data):
    # 存储数据
    pass
```

**Airflow 的方式**：

```python
# Airflow 方式：编写一个 DAG，多个 Task
from airflow import DAG
from airflow.operators.python import PythonOperator

def kafka_consumer_task():
    pass

def transform_task():
    pass

def gcs_exporter_task():
    pass

dag = DAG('supply_chain_ingestion')
load >> transform >> export
```

### 如果你坚持用 Airflow？

**需要做以下改造**：

1. 添加 Kafka 插件：`apache-airflow-providers-apache-kafka`
2. 处理 streaming + 批处理的混合模式（Airflow 不擅长流处理）
3. 编写更多的自定义代码
4. **耗时会增加 3-5 倍**

**建议**：现在学 Mage，它更适合这个项目。Airflow 是 batch 处理的王者，不是流处理。

---

## ✅ 完整的 Setup 步骤（从零开始）

### 第一步：项目结构初始化

```bash
cd /Users/liceline/Documents/study_material/data_engineer/project_study/supply_chain/supply_chain_de_study

# 创建目录结构
mkdir -p data
mkdir -p configs
mkdir -p scripts
mkdir -p docker
```

### 第二步：下载和准备数据

```bash
# 从 Kaggle 下载数据
# https://www.kaggle.com/datasets/shashwatwork/dataco-smart-supply-chain-for-big-data-analysis

# 假设你已经下载，把 CSV 放在：
cp /path/to/DataCoSupplyChainDataset.csv ./data/
```

### 第三步：创建配置文件

**文件：supply_chain_de_study/config.py**

```python
# Kafka 配置
KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'  # 本地开发
# KAFKA_BOOTSTRAP_SERVERS = 'kafka:29092'  # Docker 内部
KAFKA_TOPIC = 'supply_chain_data'

# PostgreSQL 配置（Mage 元数据存储）
POSTGRES_HOST = 'localhost'
POSTGRES_PORT = 5432
POSTGRES_USER = 'postgres'
POSTGRES_PASSWORD = 'postgres'
POSTGRES_DB = 'mage_db'

# GCS 配置（可选，初期使用本地文件系统）
GCS_PROJECT_ID = 'your-gcp-project'
GCS_BUCKET = 'your-bucket-name'
GCS_PATH = 'raw_streaming'

# CSV 文件路径
CSV_FILE_PATH = './data/DataCoSupplyChainDataset.csv'

# 生产延迟（秒）- 用于模拟流式数据
PRODUCER_DELAY = 0.5  # 每条记录延迟 0.5 秒
```

### 第四步：创建 Kafka Producer（生产者）

**文件：supply_chain_de_study/producer.py**

```python
from confluent_kafka import Producer
import json
import csv
import time
from config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC, CSV_FILE_PATH, PRODUCER_DELAY

def read_csv_rows(file_path):
    """从 CSV 读取每一行数据"""
    with open(file_path, 'r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        for row in reader:
            yield row

def delivery_report(err, msg):
    """消息发送回调函数"""
    if err is not None:
        print(f'❌ 消息发送失败: {err}')
    else:
        print(f'✅ 消息已发送到 topic: {msg.topic()}, '
              f'分区: {msg.partition()}, 偏移量: {msg.offset()}')

def produce_streaming_data():
    """主生产函数"""
    # 创建 Kafka producer
    producer = Producer({
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'client.id': 'supply_chain_producer'
    })
  
    print(f"🚀 开始从 {CSV_FILE_PATH} 生产数据到 Kafka topic: {KAFKA_TOPIC}")
  
    try:
        row_count = 0
        for row in read_csv_rows(CSV_FILE_PATH):
            # 将每一行转换为 JSON 字符串
            json_row = json.dumps(row)
          
            # 发送到 Kafka
            producer.produce(
                KAFKA_TOPIC,
                value=json_row.encode('utf-8'),
                callback=delivery_report
            )
          
            row_count += 1
          
            # 模拟流式数据的延迟
            time.sleep(PRODUCER_DELAY)
          
            # 每 100 条记录输出一次进度
            if row_count % 100 == 0:
                print(f"📊 已生产 {row_count} 条记录")
                producer.flush()  # 定期刷新
  
    except KeyboardInterrupt:
        print("\n⏸️  用户中断生产")
  
    finally:
        # 确保所有消息都被发送
        producer.flush()
        print(f"✅ 生产完成，共 {row_count} 条记录")

if __name__ == '__main__':
    produce_streaming_data()
```

### 第五步：创建 Docker Compose 文件

**文件：supply_chain_de_study/docker/docker-compose-kafka.yml**

```yaml
version: '3.8'

services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.4.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    ports:
      - "2181:2181"

  kafka:
    image: confluentinc/cp-kafka:7.4.0
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"

  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: mage_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

**文件：supply_chain_de_study/docker/docker-compose-mage.yml**

```yaml
version: '3.8'

services:
  mage:
    image: mageai/mageai:latest
    container_name: mage-pipeline
    command: mage start supply_chain_project
    environment:
      POSTGRES_DBNAME: mage_db
      POSTGRES_SCHEMA: public
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_HOST: postgres
      POSTGRES_PORT: 5432
    ports:
      - "6789:6789"
    volumes:
      - ./mage_project:/home/src
    depends_on:
      - postgres
```

### 第六步：启动服务

```bash
# 1. 启动 Kafka + PostgreSQL
docker-compose -f docker/docker-compose-kafka.yml up -d

# 等待服务启动
sleep 10

# 2. 启动 Mage
docker-compose -f docker/docker-compose-mage.yml up -d

# 等待 Mage 初始化
sleep 15

# 3. 访问 Mage UI
# 打开浏览器访问：http://localhost:6789
```

### 第七步：创建 Mage Pipeline（在 UI 中或代码中）

**在 Mage UI 中：**

1. 访问 `http://localhost:6789`
2. 点击 "Create Pipeline"
3. 选择 "Standard (Batch)" 或 "Streaming"
4. 添加三个块：
   - **Load Block**：从 Kafka 读取
   - **Transform Block**：数据处理
   - **Export Block**：写入存储

**或者直接编写代码：**

**文件：supply_chain_de_study/mage_project/pipelines/kafka_to_storage.py**

```python
from mage_ai.orchestration.triggers.api import trigger_pipeline
from mage_ai.io.kafka import KafkaConsumer
import json

@loader
def load_from_kafka():
    """从 Kafka 消费数据"""
    consumer = KafkaConsumer(
        topic='supply_chain_data',
        bootstrap_servers='kafka:29092',
        group_id='mage_consumer'
    )
  
    data = []
    for message in consumer:
        row = json.loads(message.value.decode('utf-8'))
        data.append(row)
      
        # 每 1000 条记录返回一次
        if len(data) >= 1000:
            break
  
    return data

@transformer
def transform_data(data):
    """数据转换和清洗"""
    import pandas as pd
  
    df = pd.DataFrame(data)
  
    # 数据清洗示例
    df = df.dropna()  # 删除缺失值
    df['timestamp'] = pd.Timestamp.now()
  
    return df

@exporter
def export_to_parquet(df):
    """导出为 Parquet 格式"""
    import pyarrow.parquet as pq
    from datetime import datetime
  
    # 本地存储路径（后期可改为 GCS）
    file_path = f'./data/raw_streaming/stream_{datetime.now().strftime("%Y%m%d_%H%M%S")}.parquet'
  
    df.to_parquet(file_path)
    print(f"✅ 数据已导出到 {file_path}")
```

---

## 🔌 运行流程

```bash
# 终端 1：启动 Kafka
docker-compose -f docker/docker-compose-kafka.yml up

# 终端 2：启动 Mage
docker-compose -f docker/docker-compose-mage.yml up

# 终端 3：运行 Producer（生产数据）
python producer.py

# 终端 4：在 Mage UI 中手动触发 pipeline
# 或通过 Mage API 调用
curl -X POST http://localhost:6789/api/pipeline_runs \
  -H "Content-Type: application/json" \
  -d '{"pipeline_uuid": "your_pipeline_uuid"}'
```

---

## 📊 验证数据流

```bash
# 1. 验证 Kafka topic 中是否有数据
docker exec -it <kafka-container-id> \
  kafka-console-consumer.sh \
  --bootstrap-server kafka:9092 \
  --topic supply_chain_data \
  --from-beginning \
  --max-messages 5

# 2. 查看 Mage 日志
docker logs -f <mage-container-id>

# 3. 查看生成的 Parquet 文件
ls -lh ./data/raw_streaming/
```

---

## ⚠️ 常见问题


| 问题                  | 原因            | 解决                                  |
| ----------------------- | ----------------- | --------------------------------------- |
| Producer 连接失败     | Kafka 未启动    | `docker-compose up` 并等待 10 秒      |
| Mage 无法连接到 Kafka | 网络问题        | 检查 Docker 网络，或改用`kafka:29092` |
| Parquet 文件为空      | Consumer 未运行 | 确保 Mage pipeline 已启动             |
| 内存不足              | 数据量过大      | 减小 batch 大小或调整 Docker 内存     |

---

## 🎯 本阶段关键概念总结


| 概念            | 解释                               |
| ----------------- | ------------------------------------ |
| **Kafka Topic** | 消息队列的主题，像一个频道         |
| **Producer**    | 生产者，从 CSV 读取并发送数据      |
| **Consumer**    | 消费者，读取并处理数据             |
| **Offset**      | 消费进度，记录读到哪条消息         |
| **Partition**   | 主题分区，用于并行处理             |
| **Mage Block**  | 管道的一个步骤（加载、转换、导出） |

---

## 📝 下一步

完成 Ingestion 阶段后，你将有：

- ✅ Kafka 中的实时数据流
- ✅ Parquet 格式的本地数据文件
- ✅ 在 Mage 中运行的 ETL 管道

下一步：**Transform 阶段** - 使用 Spark 处理和转换数据
