# 供应链数据流处理指南

## 架构说明

```
DataCoSupplyChainDataset.csv (本地)
    ↓
Producer (快速发送)
    ↓
Kafka Topic: supply-chain-orders
    ↓
Consumer (消费并缓冲)
    ↓
GCS: gs://supply-chain-data-bucket-485314/raw_streaming/*.parquet
```

## 快速启动

### 方法 1: 使用 Python 脚本（推荐）

```bash
cd /Users/liceline/Documents/study_material/data_engineer/project_study/supply_chain/supply_chain_de_study/streaming_pipeline/kafka

# 后台启动 Producer 和 Consumer
python run_pipeline.py

# 监控日志
tail -f ../../../logs/producer.log
tail -f ../../../logs/consumer.log
```

### 方法 2: 使用 Shell 脚本

```bash
cd /Users/liceline/Documents/study_material/data_engineer/project_study/supply_chain/supply_chain_de_study/streaming_pipeline/kafka

# 赋予执行权限
chmod +x start_pipeline.sh

# 运行脚本
./start_pipeline.sh

# 监控日志
tail -f ../../../logs/producer.log
tail -f ../../../logs/consumer.log
```

### 方法 3: 手动分别启动

```bash
cd /Users/liceline/Documents/study_material/data_engineer/project_study/supply_chain/supply_chain_de_study/streaming_pipeline/kafka

# 终端 1: 启动 Consumer
python consumer.py

# 终端 2: 启动 Producer
python producer_fast.py
```

## 文件说明

### Producer
- **producer.py** - 原始版本，流式发送（每秒 10 条，带延迟）
- **producer_fast.py** - 快速版本，批量快速发送（无延迟）

### Consumer
- **consumer.py** - 消费 Kafka 并写入 GCS
  - 自动转换为 Parquet 格式
  - 每 500 条记录批量写入
  - 支持 JSON 和 Parquet 输出

### 配置
- **kafka_config.py** - 中央配置文件
  - GCS Bucket: `supply-chain-data-bucket-485314`
  - CSV 文件: `data/DataCoSupplyChainDataset.csv`
  - Topic: `supply-chain-orders`

## 性能指标

| 指标 | 原始 Producer | 快速 Producer |
|-----|-------------|-------------|
| 速度 | ~10 条/秒 | ~5000+ 条/秒 |
| 发送时间 | ~3-5 小时 | ~5-10 分钟 |
| 模式 | 流式模拟 | 批量处理 |

## 后台运行管理

### 查看运行的进程
```bash
ps aux | grep "python.*producer\|python.*consumer"
```

### 停止特定进程
```bash
kill <PID>
```

### 查看日志
```bash
# 实时查看
tail -f logs/producer.log
tail -f logs/consumer.log

# 查看最后 N 行
tail -100 logs/producer.log
```

## Airflow 自动化

### 环境要求
- Airflow 已在 `docker/airflow` 启动
- DAG 文件位置: `docker/airflow/dags/kafka_supply_chain_pipeline.py`

### 使用方法

1. **部署 DAG**
   ```bash
   cp streaming_pipeline/kafka/airflow_dag.py docker/airflow/dags/
   ```

2. **Airflow UI 中触发**
   - 访问 http://localhost:8080
   - 查找 DAG: `kafka_supply_chain_pipeline`
   - 点击 "Trigger DAG"

3. **命令行触发**
   ```bash
   cd docker/airflow
   docker compose exec airflow-scheduler airflow dags trigger kafka_supply_chain_pipeline
   ```

### DAG 流程
```
安装依赖 → Producer 发送数据 → Consumer 消费数据 → 验证上传
```

## 故障排除

### 问题 1: Consumer 无法连接 GCS
**原因**: 缺少 GCP 凭据

**解决**:
```bash
# 检查文件
ls -la keys/gcp-cred.json

# 检查权限
cat keys/gcp-cred.json | grep "type"
```

### 问题 2: Producer 超时
**原因**: CSV 文件过大或网络问题

**解决**:
- 增加超时: 修改 `producer_fast.py` 中的 `timeout=30`
- 检查 Kafka: `docker compose -f docker/kafka/docker-compose.yaml ps`

### 问题 3: 内存不足
**原因**: 缓冲区过大

**解决**:
- 减小缓冲区: 修改 `consumer.py` 中 `self.buffer_size = 100`

## 监控检查点

### 1. Kafka 健康检查
```bash
docker compose -f docker/kafka/docker-compose.yaml ps
```

### 2. GCS 验证
```bash
# 列出 raw_streaming 文件夹中的 Parquet 文件
gsutil ls gs://supply-chain-data-bucket-485314/raw_streaming/

# 查看单个文件
gsutil cat gs://supply-chain-data-bucket-485314/raw_streaming/orders_20240101_120000.parquet | head -c 1000
```

### 3. 数据验证
```python
import pandas as pd
from google.cloud import storage

# 读取 GCS 中的 Parquet 文件
client = storage.Client()
bucket = client.bucket('supply-chain-data-bucket-485314')
blob = bucket.blob('raw_streaming/orders_20240101_120000.parquet')
df = pd.read_parquet(blob.open('rb'))
print(df.head())
```

## 下一步

- [ ] 监控数据管道运行情况
- [ ] 验证 GCS 中的数据
- [ ] 在 Airflow 中设置自动化调度
- [ ] 添加数据质量检查
- [ ] 集成到 dbt 或其他数据变换工具

---

**最后更新**: 2024-01-31
