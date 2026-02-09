# Batch Data 获取与处理详解

## 1. Batch Data 来源

### 1.1 数据源位置
- **GCS 路径**：`gs://supply-chain-data-terraform/raw_streaming/`
- **数据格式**：Parquet 文件
- **生成方式**：由流式管道（Mage + Kafka）持续写入
- **包含内容**：嵌套JSON结构，包含业务数据与元数据

### 1.2 数据结构（嵌套JSON）

```json
{
  "data": {
    // 客户维度字段
    "Customer Id": "C123",
    "Customer Email": "customer@example.com",
    "Customer Fname": "John",
    "Customer Lname": "Doe",
    "Customer Segment": "Premium",
    "Customer City": "New York",
    // ... 更多客户字段
    
    // 产品维度字段
    "Product Card Id": "P456",
    "Product Category Id": "CAT789",
    "Category Name": "Electronics",
    "Product Description": "...",
    "Product Price": 99.99,
    // ... 更多产品字段
    
    // 订单维度字段
    "Order Id": "ORD001",
    "Order date (DateOrders)": "2024-01-15",
    "Sales": 1500.50,
    "Order Status": "Completed",
    // ... 更多订单字段
    
    // 运输维度字段
    "Shipping Mode": "Ship",
    "Days for shipping (real)": 5,
    "Delivery Status": "Delivered",
    // ... 更多运输字段
    
    // 位置维度字段
    "Order Zipcode": "10001",
    "Order City": "New York",
    "Latitude": 40.7128,
    // ... 更多位置字段
    
    // 部门维度字段
    "Department Id": "D001",
    "Department Name": "Sales",
    // ... 更多部门字段
  },
  "metadata": {
    "key": "...",
    "offset": 12345,
    "partition": 0,
    "time": "2024-01-15T10:30:00Z",
    "topic": "supply_chain_data"
  }
}
```

---

## 2. Batch 处理流程（Spark Pipeline）

### 2.1 处理步骤图解

```
┌─────────────────────────────────────────────────────────────┐
│ 第1步：加载原始数据                                           │
│ 源：GCS gs://supply-chain-data-terraform/raw_streaming/*    │
│ 格式：Parquet （多个文件，包含完整批次）                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────────┐
         │ 第2步：创建 Spark Session  │
         │ ✓ 连接 GCS 服务账号认证    │
         │ ✓ 配置 Hadoop GCS连接    │
         │ ✓ JAR依赖加载            │
         └───────────────┬───────────┘
                         │
                         ▼
        ┌────────────────────────────────┐
        │ 第3步：提取维度表（7个）       │
        │ ├─ customer_dimension          │
        │ ├─ product_dimension           │
        │ ├─ location_dimension          │
        │ ├─ order_dimension             │
        │ ├─ shipping_dimension          │
        │ ├─ department_dimension        │
        │ └─ metadata_dimension          │
        └────────────┬───────────────────┘
                     │
                     ▼
        ┌────────────────────────────────┐
        │ 第4步：字段提取与清洗          │
        │ ✓ 从嵌套 data 提取字段        │
        │ ✓ 从 metadata 提取元数据      │
        │ ✓ 列名标准化（重命名冲突）    │
        │ ✓ 去重（可选）                │
        └────────────┬───────────────────┘
                     │
                     ▼
        ┌────────────────────────────────┐
        │ 第5步：写入 GCS 转换数据       │
        │ 目标：gs://supply-chain-data   │
        │       /transformed_data/      │
        │ 格式：Parquet                 │
        │ 文件：*_dimension.parquet     │
        │ 模式：overwrite（覆盖）       │
        └────────────┬───────────────────┘
                     │
                     ▼
        ┌────────────────────────────────┐
        │ ✅ 完成：Spark 处理完毕        │
        │ 生成7个维度表（Silver级）     │
        └────────────────────────────────┘
```

### 2.2 关键代码实现

**配置信息**（[config.py](export_to_gcs/config.py)）：
```python
credentials_path = './docker/mage/google-cred.json'          # GCS 认证凭证
jar_file_path = "./docker/spark/jar_files/gcs-connector-..."  # GCS Hadoop 连接器
gcs_bucket_path = "gs://supply-chain-data-terraform/"         # 源桶
output_path = gcs_bucket_path + "transformed_data/"           # 目标桶
```

**Spark 配置**（[pipeline.py](export_to_gcs/pipeline.py) 摘要）：
```python
# 1. Spark 配置
conf = SparkConf() \
    .setMaster('local[*]')  # 本地多核模式
    .setAppName('test')
    .set("spark.jars", jar_file_path)  # 加载 GCS JAR
    .set("spark.hadoop.google.cloud.auth.service.account.enable", "true")
    .set("spark.hadoop.google.cloud.auth.service.account.json.keyfile", credentials_path)

# 2. 加载原始数据
df_raw = spark.read.parquet(gcs_bucket_path + 'raw_streaming/*')

# 3. 提取维度
def extract_columns(df, columns_to_extract):
    # 从嵌套的 "data" 字段中提取指定列
    extracted_cols = [col("data").getItem(col_name).alias(col_name) 
                      for col_name in columns_to_extract]
    return df.select(*extracted_cols)

# 4. 创建维度表示例
customer_dimension = extract_columns(df_raw, customer_columns)
product_dimension = extract_columns(df_raw, product_columns)
# ... 其他维度表

# 5. 写入 GCS
def write_to_gcs(dataframes, output_path):
    for name, dataframe in dataframes.items():
        dataframe.write \
            .mode("overwrite") \
            .option("header", "true") \
            .option("compression", "none") \
            .parquet(output_path + name + ".parquet")
```

### 2.3 提取的维度表详情

| 维度表 | 源列 (来自 utils.py) | 行数 | 描述 |
|------|------------------|------|------|
| **customer_dimension** | Customer Id, Email, Name, Segment, Location... | ~100k | 客户主维度 |
| **product_dimension** | Product Id, Category, Name, Price, Status... | ~5k | 产品主维度 |
| **location_dimension** | Order Zipcode, City, State, Latitude, Longitude... | ~50k | 地理位置维度 |
| **order_dimension** | Order Id, Date, Customer Id, Sales, Status... | ~500k | 订单维度 |
| **shipping_dimension** | Shipping Date, Days, Mode, Delivery Status... | ~500k | 运输维度 |
| **department_dimension** | Department Id, Name, Market... | ~10 | 部门维度 |
| **metadata_dimension** | key, offset, partition, time, topic | 变化 | 管道元数据 |

**字段提取来源**（[utils.py](export_to_gcs/utils.py)）：
```python
customer_columns = ["Customer Id", "Customer Email", "Customer Fname", 
                    "Customer Lname", "Customer Segment", "Customer City", ...]

product_columns = ["Product Card Id", "Product Category Id", "Category Name",
                   "Product Description", "Product Image", ...]

order_columns = ["Order Id", "Order date (DateOrders)", "Order Customer Id",
                 "Order Item Quantity", "Sales", "Order Status", ...]

# ... 其他维度列定义
```

---

## 3. 导出到 BigQuery（Mage Pipeline）

### 3.1 流程概览

```
GCS transformed_data/
  ├─ customer_dimension.parquet
  ├─ product_dimension.parquet
  ├─ location_dimension.parquet
  ├─ order_dimension.parquet
  ├─ shipping_dimension.parquet
  ├─ department_dimension.parquet
  └─ metadata_dimension.parquet
         │
         ▼
   ┌─────────────────────┐
   │ Mage Pipeline       │
   │ export_to_big_query │
   └────────┬────────────┘
         │
    ┌────┴────────────────────────────────────────┐
    │                                              │
    ▼                                              ▼
┌─────────────┐  ┌─────────────┐  ...  ┌─────────────┐
│ Data Loader │  │ Transformer │  ... │ Exporter    │
│ (读取GCS)   │  │ (格式转换)  │      │ (写入BQ)    │
└─────┬───────┘  └──────┬──────┘      └──────┬──────┘
      │                 │                    │
      └─────────────────┼────────────────────┘
                        │
                        ▼
         BigQuery 数据集: supply_chain_data
         ┌──────────────────────────────────────┐
         │ 表:                                  │
         │ ├─ dim_customer                      │
         │ ├─ dim_product                       │
         │ ├─ dim_location                      │
         │ ├─ dim_order                         │
         │ ├─ dim_shipping                      │
         │ ├─ dim_department                    │
         │ └─ dim_metadata                      │
         └──────────────────────────────────────┘
```

### 3.2 导出脚本示例

**文件路径**：[export_to_big_query/data_exporters/customer_dim_to_big_query.py](export_to_big_query/data_exporters/customer_dim_to_big_query.py)

```python
from mage_ai.io.bigquery import BigQuery
from pandas import DataFrame

@data_exporter
def export_data_to_big_query(df: DataFrame, **kwargs) -> None:
    """导出客户维度表到 BigQuery"""
    
    # BigQuery 表 ID (项目.数据集.表)
    table_id = 'gothic-sylph-387906.supply_chain_data.dim_customer'
    
    config_path = path.join(get_repo_path(), 'io_config.yaml')
    config_profile = 'default'
    
    # 导出配置
    BigQuery.with_config(
        ConfigFileLoader(config_path, config_profile)
    ).export(
        df,                 # DataFrame (来自前置 loader/transformer)
        table_id,          # 目标表
        if_exists='replace'  # 如果表存在则覆盖
    )
```

**7个导出脚本对应表**：
- `customer_dim_to_big_query.py` → `dim_customer`
- `product_dim_to_big_query.py` → `dim_product`
- `location_dim_to_big_query.py` → `dim_location`
- `order_dim_to_big_query.py` → `dim_order`
- `shipping_dim_to_big_query.py` → `dim_shipping`
- `department_dim_to_big_query.py` → `dim_department`
- `metadata_dim_to_big_query.py` → `dim_metadata`

### 3.3 Mage Pipeline 配置

**位置**：[export_to_big_query/](export_to_big_query/)

```yaml
# metadata.yaml
name: export_to_big_query
type: python
blocks:
  - name: data_loaders
    # 读取 GCS 中的 Parquet 文件
  - name: data_exporters
    # 导出到 BigQuery 各表
```

---

## 4. 完整 Batch 处理时间轴

```
时间流向 →

T0          T1              T2                  T3              T4
│           │               │                   │               │
└─ Start ──┬─ Load          │                   │               │
           │ from GCS       │                   │               │
           │                │                   │               │
           └──────┬─ Extract              │               │
                  │ Dimensions            │               │
                  │ (7个维度表)            │               │
                  │                       │               │
                  └────────┬─ Write       │               │
                           │ to GCS      │               │
                           │             │               │
                           └──────┬─ Mage           │
                                  │ Pipeline         │
                                  │ Loads & Exports  │
                                  │                  │
                                  └────────┬─ BigQuery
                                           │ Tables Ready
                                           │ (Silver Level)
                                           │
                                           └──► ✅ 完成

持续时间估算：
- 加载 raw_streaming: 1-3 分钟 (取决于数据量)
- 提取 7 个维度表: 2-5 分钟 (Spark 并行处理)
- 写入 GCS 转换数据: 1-2 分钟
- Mage 导出到 BigQuery: 2-5 分钟
─────────────────────────────
总耗时: 6-15 分钟 (首次) / 3-8 分钟 (增量)
```

---

## 5. 执行命令与流程对应

### 5.1 启动 Spark 集群
```bash
start-spark
```
**作用**：
- 构建 Spark Docker 镜像（首次）
- 启动 Spark Master 与 Worker 容器
- 暴露 8080 (UI) 与 7077 (交互) 端口

### 5.2 运行 OLAP 转换
```bash
olap-transformation-pipeline
```
**等同于**：
```bash
python batch_pipeline/export_to_gcs/pipeline.py
```
**执行内容**：
1. 连接 GCS 获取 service 账号凭证
2. 读取 `gs://supply-chain-data-terraform/raw_streaming/*` 的所有 Parquet 文件
3. 提取 7 个维度表
4. 写入 `gs://supply-chain-data-terraform/transformed_data/` (7 个 Parquet 文件)

### 5.3 运行 GCS-to-BigQuery 导出
```bash
gcs-to-bigquery-pipeline
```
**实际执行**：
```bash
curl -X POST http://127.0.0.1:6789/api/pipeline_schedules/2/pipeline_runs/... \
  --header 'Content-Type: application/json' \
  --data '{...}'
```
**执行内容**：
1. 触发 Mage 的 `export_to_big_query` pipeline
2. 对每个维度表（customer, product, order 等）：
   - 从 GCS Parquet 读取
   - 转换为 Pandas DataFrame
   - 导出到 BigQuery（表名：`dim_*`）

### 5.4 一键执行 Batch
```bash
start-batch-pipeline
```
**等同于**：
```bash
start-spark
olap-transformation-pipeline
gcs-to-bigquery-pipeline
```

---

## 6. 数据质量检查点

| 检查点 | 内容 | 验证命令 |
|------|------|---------|
| **原始数据** | GCS raw_streaming 是否有数据 | `gsutil ls gs://supply-chain-data-terraform/raw_streaming/` |
| **Spark 转换** | 维度表是否生成 | `gsutil ls gs://supply-chain-data-terraform/transformed_data/` |
| **BigQuery 导入** | 表是否创建与有数据 | `bq ls -t supply_chain_data` |
| **行数验证** | 维度表行数是否合理 | `bq query "SELECT COUNT(*) FROM supply_chain_data.dim_customer"` |

---

## 7. 常见问题与排查

### 问题1：Spark 无法连接 GCS
**症状**：`FileNotFoundException` 或 `EOFException`
**排查**：
```bash
# 检查凭证文件是否存在
ls -la ./docker/mage/google-cred.json

# 检查 Spark 配置是否正确指定
grep "google-cred.json" batch_pipeline/export_to_gcs/pipeline.py
```

### 问题2：Mage API 无法调用
**症状**：`Connection refused` 或 `404 Not Found`
**排查**：
```bash
# 检查 Mage 是否启动
docker ps | grep mage

# 检查 API 端点是否正确
curl -v http://127.0.0.1:6789/health
```

### 问题3：BigQuery 表未创建
**症状**：导出完成但 BigQuery 无表
**排查**：
```bash
# 检查 BigQuery 权限
gcloud projects get-iam-policy gothic-sylph-387906

# 查询 Mage 日志
docker logs <mage-container-id>
```

---

## 8. 性能优化建议

| 优化方向 | 方法 |
|--------|------|
| **Spark 并行度** | 调整 `setMaster('local[*]')` → `setMaster('spark://master:7077')` 用于分布式 |
| **GCS 批量操作** | 增加 `spark.hadoop.fs.gs.batch.size` 参数 |
| **BigQuery 写入** | 使用 `load_job_config` 的 `write_disposition='WRITE_TRUNCATE'` 替代 `WRITE_APPEND` |
| **增量处理** | 添加时间戳过滤，只处理新增数据 |

---

## 参考文件速览

| 文件 | 用途 |
|------|------|
| [batch_pipeline.md](batch_pipeline.md) | 批处理总体说明 |
| [export_to_gcs/pipeline.py](export_to_gcs/pipeline.py) | Spark OLAP 转换脚本 |
| [export_to_gcs/config.py](export_to_gcs/config.py) | 配置（凭证、桶路径） |
| [export_to_gcs/utils.py](export_to_gcs/utils.py) | 列定义（7个维度） |
| [export_to_big_query/data_exporters/](export_to_big_query/data_exporters/) | Mage 导出脚本（7个） |
| [export_to_big_query/metadata.yaml](export_to_big_query/metadata.yaml) | Mage Pipeline 配置 |

