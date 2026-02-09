# 数据获取与处理流程图

## 1. 高层数据流程架构

```
┌─────────────────┐
│  数据源          │
│  - CSV文件       │
│  - 离线门店事件   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│  1️⃣ 数据采集 (Data Ingestion)   │
│  Producer (Docker Container)    │
│  ✓ 读取CSV数据                  │
│  ✓ 生成实时事件                  │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  2️⃣ 消息队列 (Kafka)            │
│  Topic: "supply_chain_data"     │
│  ✓ 实时数据流                    │
│  ✓ 分布式处理                    │
└────────┬────────────────────────┘
         │
    ┌────┴────┐
    │          │
    ▼          ▼
┌──────────────┐  ┌─────────────────────────────┐
│ PostgreSQL   │  │ 3️⃣ GCS (Bronze级数据)      │
│ (Bronze级)   │  │ ✓ raw_streaming 文件夹      │
│ 本地数据库   │  │ ✓ 未处理的原始数据          │
└──────────────┘  └────────┬────────────────────┘
                           │
                           ▼
                  ┌─────────────────────────────┐
                  │ 4️⃣ Spark OLAP转换          │
                  │ (Batch Pipeline)           │
                  │ ✓ 清洗数据                  │
                  │ ✓ 聚合转换                  │
                  │ ✓ 构建星型模型              │
                  │ ✓ 生成维度表/事实表          │
                  └────────┬────────────────────┘
                           │
                           ▼
                  ┌─────────────────────────────┐
                  │ GCS (Silver级数据)         │
                  │ ✓ transformed 文件夹       │
                  │ ✓ 已处理的结构化数据       │
                  └────────┬────────────────────┘
                           │
                           ▼
                  ┌─────────────────────────────┐
                  │ 5️⃣ Mage导出管道            │
                  │ (gcs-to-bigquery)         │
                  │ ✓ 读取GCS数据              │
                  │ ✓ 导入BigQuery            │
                  └────────┬────────────────────┘
                           │
                           ▼
                  ┌─────────────────────────────┐
                  │ BigQuery (Silver级)        │
                  │ ✓ 云数据仓库               │
                  │ ✓ 结构化表格               │
                  └────────┬────────────────────┘
                           │
                           ▼
                  ┌─────────────────────────────┐
                  │ 6️⃣ DBT 业务转换             │
                  │ (dbt run)                  │
                  │ ✓ 创建聚合表               │
                  │ ✓ 创建业务视图              │
                  │ ✓ 创建KPI计算表             │
                  └────────┬────────────────────┘
                           │
                           ▼
                  ┌─────────────────────────────┐
                  │ BigQuery (Gold级数据)      │
                  │ ✓ 业务转换完成              │
                  │ ✓ 开放分析与使用            │
                  └────────┬────────────────────┘
                           │
                           ▼
                  ┌─────────────────────────────┐
                  │ 7️⃣ 可视化与分析             │
                  │ Metabase/Looker           │
                  │ ✓ 仪表板                   │
                  │ ✓ 报表                     │
                  │ ✓ 实时监控                 │
                  └─────────────────────────────┘
```

---

## 2. 详细流程说明

### 第1阶段：数据采集 (Data Ingestion)
| 组件 | 描述 | 输出 |
|------|------|------|
| **Source** | CSV文件 + 离线门店事件 | 原始事件记录 |
| **Producer** | Docker 容器中的 Python 脚本 | 发送到Kafka topic |
| **Kafka Topic** | `supply_chain_data` | 实时事件流 |

**关键文件：** [streaming_pipeline/producer.py](../../streaming_pipeline/producer.py)

---

### 第2阶段：流式数据收集 (Streaming Pipeline via Mage)
```
Kafka Topic
    ↓
Mage Pipeline: kafka_to_gcs_streaming
    ├─ Data Loader: consume_from_kafka.yaml
    │  └─ 每批消费1000条消息
    │
    ├─ Transform: (可选的中间处理)
    │
    └─ Data Exporter: kafka_to_gcs.yaml
       └─ 写入 GCS bucket: raw_streaming/
```

**数据位置：**
- Bronze 级（原始）：GCS `raw_streaming/` 文件夹
- 备份：PostgreSQL 表

**关键文件：**
- [streaming_pipeline/kafka_to_gcs_streaming/consume_from_kafka.yaml](../../streaming_pipeline/kafka_to_gcs_streaming/consume_from_kafka.yaml)
- [streaming_pipeline/kafka_to_gcs_streaming/kafka_to_gcs.yaml](../../streaming_pipeline/kafka_to_gcs_streaming/kafka_to_gcs.yaml)

---

### 第3阶段：批处理与OLAP转换 (Spark Pipeline)
```
GCS raw_streaming/
    ↓
Spark Job: batch_pipeline/export_to_gcs/pipeline.py
    ├─ 读取 raw 数据
    ├─ 数据清洗（去重、NULL处理）
    ├─ 维度提取（Customer, Product, Order, etc.）
    ├─ 构建星型模型
    │  ├─ 事实表 (Fact Tables)
    │  └─ 维度表 (Dimension Tables)
    ├─ 数据聚合与计算
    └─ 写入 GCS transformed/
```

**转换后数据结构（Silver 级）：**
- `dim_customer.parquet` - 客户维度表
- `dim_product.parquet` - 产品维度表
- `dim_order.parquet` - 订单维度表
- `dim_shipping.parquet` - 物流维度表
- `fact_sales.parquet` - 销售事实表（示例）

**关键文件：** [batch_pipeline/export_to_gcs/pipeline.py](../../batch_pipeline/export_to_gcs/pipeline.py)

---

### 第4阶段：导出到BigQuery
```
GCS transformed/
    ↓
Mage Pipeline: export_to_big_query
    ├─ Data Loader: 读取GCS
    │
    ├─ Transform: 格式转换 (Parquet → BigQuery Tables)
    │
    └─ Data Exporter: 导入BigQuery
       └─ 创建表: customer_dim, product_dim, order_dim, etc.
```

**BigQuery 表位置：**
- Dataset: `supply_chain` (或项目配置的名称)
- Tables: `dim_*`, `fact_*`

**关键文件：**
- [batch_pipeline/export_to_big_query/data_loaders/](../../batch_pipeline/export_to_big_query/data_loaders/)
- [batch_pipeline/export_to_big_query/data_exporters/](../../batch_pipeline/export_to_big_query/data_exporters/)

---

### 第5阶段：DBT业务转换 (Gold 级)
```
BigQuery Tables (Silver)
    ↓
dbt run
    ├─ Staging Models (dim_* 标准化)
    │
    └─ Core Models (业务聚合)
       ├─ customer_retention_rate
       ├─ financial_commitments
       ├─ fraud_detection
       ├─ inventory_levels
       ├─ overall_performance
       └─ payment_delays
```

**DBT模型位置：**
- 分层模型：[business_transformations/models/](../../business_transformations/models/)
  - `staging/` - 数据标准化
  - `core/` - 业务指标计算

**关键文件：** [business_transformations/dbt_pipeline.md](../../business_transformations/dbt_pipeline.md)

---

### 第6阶段：可视化与分析
```
BigQuery (Gold 级表)
    ↓
Metabase/Looker
    ├─ 连接 BigQuery
    ├─ 创建仪表板 (Dashboards)
    ├─ 实时监控关键指标
    │  ├─ 库存水平
    │  ├─ 付款延迟
    │  ├─ 客户留存率
    │  ├─ 欺诈检测
    │  └─ 财务承诺
    └─ 生成报表与告警
```

---

## 3. 数据格式演变

```
┌─────────────────────────────────────────────────────────┐
│ CSV/JSON (CSV 文件 → 内存)                              │
│ 示例: product, customer, order, shipping 信息            │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────▼────────────┐
        │ Kafka (行序列化)        │
        │ Topic: supply_chain_data│
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────┐
        │ GCS (raw_streaming)     │
        │ 格式: CSV/JSON 行       │
        │ 数据段: 未处理          │
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────┐
        │ Spark 处理              │
        │ 清洗 + 聚合             │
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────┐
        │ GCS (transformed)       │
        │ 格式: Parquet           │
        │ 结构: 列式存储          │
        │ 表: dim_*, fact_*       │
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────┐
        │ BigQuery (Silver)       │
        │ 格式: 原生表            │
        │ 模式: 星型架构          │
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────┐
        │ DBT 模型化              │
        │ 业务逻辑转换            │
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────┐
        │ BigQuery (Gold)         │
        │ KPI/聚合表              │
        │ 用户友好格式            │
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────┐
        │ Metabase 仪表板        │
        │ 可视化呈现              │
        └────────────────────────┘
```

---

## 4. 完整流程时序图

```
时间线 →

T0       T1         T2              T3              T4              T5
│        │          │               │               │               │
▼        ▼          ▼               ▼               ▼               ▼
│    启动   │    数据流入     │    批处理开始  │    导出至BQ    │    DBT执行    │    仪表板
├─────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────▶
│         │              │              │              │              │
│    Kafka │  raw_streaming│   Spark     │   BigQuery   │   Gold级     │  可视化
│   启动   │  (Bronze)     │  (Silver)   │  (Silver)    │  表创建      │  数据
│         │              │              │              │              │
└─────────┴──────────────┴──────────────┴──────────────┴──────────────┴──────────

数据可用性阶段：
- 第1-2分钟：原始数据进入Kafka与GCS
- 第2-10分钟：Spark批处理生成维度表
- 第10-15分钟：数据导入BigQuery
- 第15-20分钟：DBT创建金层业务表
- 第20+分钟：仪表板可展示最新数据
```

---

## 5. 关键数据流向总结

| 来源 | 处理 | 中间存储 | 最终存储 | 用途 |
|------|------|---------|---------|------|
| CSV | 生产者 | Kafka | GCS (raw) | 原始记录备份 |
| Kafka | Mage | GCS | PostgreSQL | Bronze级审计 |
| GCS (raw) | Spark | 内存 | GCS (transformed) | Silver级分析 |
| GCS (silver) | Mage | BigQuery | BigQuery | 中期查询 |
| BigQuery | DBT | 虚拟 | BigQuery | Gold级BI使用 |
| BigQuery (gold) | - | - | Metabase | 仪表板 & 报表 |

---

## 6. 执行命令与对应流程

```bash
# 启动流式管道（第1-2阶段）
source commands.sh
start-streaming-pipeline
# 等同于:
# - start-kafka           → Kafka启动
# - start-mage            → Mage启动 (加载流式配置)
# - stream-data           → 生产者容器运行

# 启动批处理（第3-4阶段）
start-spark
start-batch-pipeline
# 等同于:
# - start-spark           → Spark集群启动
# - olap-transformation-pipeline  → python batch_pipeline/export_to_gcs/pipeline.py
# - gcs-to-bigquery-pipeline      → 触发Mage导出

# 执行DBT（第5阶段）
dbt run

# 启动仪表板（第6阶段）
start-metabase
# 访问: http://localhost:3000
```

---

## 7. 系统架构图（技术栈视图）

```
数据源            采集层           处理层              存储层              应用层
────────          ────────         ──────              ──────              ──────

CSV文件    ┐                                        ┌─ PostgreSQL      ┌─ Metabase
           │                                        │                  │
事件流     ├─→ Producer ─→ Kafka ─→ Mage ─┬─→ GCS │                  ├─ Looker
           │                          (kafka_to_gcs) ├─ BigQuery (Silver) │
离线门店   ┘                                      └─ BigQuery (Gold)   └─ 自定义API
                                     │
                                     │
                                   Spark ──────→ GCS ──────┘
                                  (OLAP)    (transformed)
                                     │
                                     ▼
                                    DBT
                                  (业务逻辑)
```

---

## 关键文件参考
- 项目主文档：[README.md](README.md)
- 流式管道说明：[streaming_pipeline/streaming_pipeline.md](streaming_pipeline/streaming_pipeline.md)
- 批处理说明：[batch_pipeline/batch_pipeline.md](batch_pipeline/batch_pipeline.md)
- DBT说明：[business_transformations/dbt_pipeline.md](business_transformations/dbt_pipeline.md)
- Docker说明：[docker/docker.md](docker/docker.md)
- 启动脚本：[commands.sh](commands.sh)
