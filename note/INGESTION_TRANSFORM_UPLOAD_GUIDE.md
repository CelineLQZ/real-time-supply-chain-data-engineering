# 项目复现指南：Ingestion → Transform → Upload

## 📋 项目数据流程（三阶段）

```
Ingestion (数据获取) → Transform (数据转换) → Upload (数据上传)
     ↓                    ↓                    ↓
  Kafka/CSV         Spark/DBT          GCS→BigQuery
```

---

## **第一阶段：Ingestion（数据获取）**

### 涉及的组件：
1. **Kafka** - 消息队列
2. **Streaming Producer** - 数据生产者（从 CSV 读取）
3. **Mage Consumer** - 从 Kafka 消费数据

### 需要的 Setup：

**1. 创建必要的目录和配置**
```bash
cd /Users/liceline/Documents/study_material/data_engineer/project_study/supply_chain/supply_chain_de

# 配置 GCP 凭证
mkdir -p ./docker/mage
# 需要放入 google-cred.json（从 GCP 获取）
```

**2. 安装依赖**
```bash
pip install -r requirements.txt
# 需要的包：pyspark, confluent_kafka, dbt
```

**3. 启动 Kafka**
```bash
source commands.sh
start-kafka
# 等待 5 秒让 Kafka 完全启动
sleep 5
```

**4. 启动数据生产（Streaming）**
```bash
stream-data  # 或：docker-compose -f ./docker/streaming/docker-compose.yaml up
```

这一阶段会：
- 读取 `./streaming_pipeline/data/` 中的 CSV 文件
- 将数据发送到 Kafka topic `supply_chain_data`
- 数据会被暂存在内存中等待处理

---

## **第二阶段：Transform（数据转换）**

### 2.1 **Spark 转换（Raw → Silver）**

**涉及的组件：**
- Apache Spark
- GCS 存储桶

**执行步骤：**

```bash
# 1. 启动 Spark 集群
start-spark
# 这会构建 Spark Docker 镜像并启动主节点和工作节点

# 2. 运行 OLAP 转换管道
olap-transformation-pipeline
# 执行：python batch_pipeline/export_to_gcs/pipeline.py
```

**发生的事情：**
- 从 Kafka 消费数据（或从 GCS `raw_streaming/` 读取）
- 提取 7 个维度表：
  - customer_dimension
  - product_dimension
  - location_dimension
  - order_dimension
  - shipping_dimension
  - department_dimension
  - metadata_dimension
- 存储为 Parquet 格式到 GCS 的 `transformed/` 路径（Silver 层）

### 2.2 **Mage 消费 Kafka → GCS**

```bash
# 1. 启动 Mage
start-mage

# 2. Mage 会自动将 Kafka 数据写入 GCS raw_streaming/ 目录
# 这个过程在后台运行
```

---

## **第三阶段：Upload（数据上传到 BigQuery）**

### 涉及的组件：
- Mage Pipeline
- Google BigQuery
- Terraform 配置的基础设施

**执行步骤：**

```bash
# 1. 确保 Terraform 已配置 BigQuery 数据集
cd ./terraform
terraform init
terraform apply

# 2. 返回主目录
cd ..

# 3. 运行 Mage 的 GCS → BigQuery 导出管道
# (通过 API 调用或 Mage UI)
# 命令集中可能有相关函数，或在 Mage UI 中手动触发
```

**发生的事情：**
- 从 GCS `transformed/` 读取 Silver 层数据
- 导入到 BigQuery 的 `terraform_bigquery` 数据集
- 数据可用于分析和 DBT 转换

---

## **完整的一键启动脚本建议**

创建一个新的启动脚本 `start-full-pipeline.sh`：

```bash
#!/bin/bash

echo "🚀 开始 Ingestion → Transform → Upload 流程"

# Step 1: Ingestion
echo "📥 第一阶段：数据获取（Ingestion）"
source commands.sh
start-kafka
sleep 5
start-mage
sleep 5
stream-data &
STREAM_PID=$!
sleep 10

# Step 2: Transform
echo "🔄 第二阶段：数据转换（Transform）"
start-spark
sleep 10
olap-transformation-pipeline

# Step 3: Upload
echo "📤 第三阶段：数据上传（Upload）"
cd terraform
terraform apply -auto-approve
cd ..

# 运行 Mage BigQuery 导出管道
echo "⬆️  导出到 BigQuery..."
# 这里需要调用 Mage API 或在 UI 中手动触发

echo "✅ 流程完成！"
```

---

## **关键文件位置**

| 文件 | 用途 |
|------|------|
| streaming_pipeline/producer.py | 数据生产者 |
| streaming_pipeline/consumer.py | Kafka 消费者 |
| batch_pipeline/export_to_gcs/pipeline.py | Spark 转换脚本 |
| batch_pipeline/export_to_big_query/ | Mage BigQuery 导出配置 |
| terraform/main.tf | GCP 基础设施配置 |

---

## **常见问题排查**

| 问题 | 解决方案 |
|------|--------|
| GCP 凭证错误 | 需要在 `./docker/mage/` 放入 `google-cred.json` |
| Kafka 连接失败 | 检查 Kafka 是否完全启动（等待 10 秒） |
| GCS 权限错误 | 确保 GCP 服务账号有足够权限 |
| Spark 内存不足 | 调整 Docker Compose 中的内存限制 |

---

## **架构概览**

### Ingestion 阶段数据流
```
CSV 文件 → Producer → Kafka Topic → Mage Consumer → GCS raw_streaming/
```

### Transform 阶段数据流
```
GCS raw_streaming/ → Spark Pipeline → 维度表提取 → GCS transformed/ (Silver)
```

### Upload 阶段数据流
```
GCS transformed/ → Mage Pipeline → BigQuery terraform_bigquery 数据集
```

---

## **Tech Stack 对应关系**

| 阶段 | 技术栈 | 作用 |
|------|--------|------|
| Ingestion | Kafka + Mage | 实时数据摄入 |
| Transform | Spark + Python | 数据清洗与维度提取 |
| Upload | Mage + Terraform | 数据导入与基础设施管理 |
| Analysis | DBT + BigQuery | 数据建模与分析 |
| Visualization | Metabase | 可视化与仪表板 |

---

## **执行验证检查清单**

- [ ] GCP 凭证文件已配置
- [ ] Docker 已安装且运行正常
- [ ] Python 依赖已安装 (pyspark, confluent_kafka, dbt)
- [ ] Kafka 成功启动在 port 29092
- [ ] Streaming producer 正在运行
- [ ] Mage 容器运行并且 UI 可访问 (localhost:6789)
- [ ] Spark 集群已启动
- [ ] GCS 存储桶已创建
- [ ] BigQuery 数据集已创建
- [ ] Terraform 状态文件已初始化

---

## **性能优化建议**

1. **Batch 大小优化** - 调整 Kafka batch 大小以平衡吞吐量和延迟
2. **Spark 分区** - 根据数据量调整 Spark 分区数
3. **GCS 存储类** - 使用 Standard 存储用于经常访问的数据
4. **BigQuery 槽位** - 考虑使用 BigQuery 槽位以获得稳定的性能

