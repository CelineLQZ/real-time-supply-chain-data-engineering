# Batch Pipeline 执行完整指南

## 目录
- [概述](#概述)
- [Docker Spark 环境配置](#docker-spark-环境配置)
- [执行步骤详解](#执行步骤详解)
- [性能优化建议](#性能优化建议)
- [常见问题排查](#常见问题排查)

---

## 概述

本文档记录了运行 `batch_pipeline/data_modeling/transformed_data.py` 的完整流程，包括：
- Docker Spark 集群的配置与启动
- GCS 连接器的集成
- Java 环境配置
- Pipeline 执行过程
- 性能优化策略

**执行时间参考**：初始配置约 1 小时（包含数据读取、转换和写入）

---

## Docker Spark 环境配置

### 1. 目录结构
```
docker/spark/
├── cluster-base.Dockerfile       # 基础镜像：Java 17 + Python
├── spark-base.Dockerfile         # Spark 基础镜像
├── spark-master.Dockerfile       # Spark Master 节点
├── spark-worker.Dockerfile       # Spark Worker 节点
├── jupyterlab.Dockerfile         # JupyterLab 镜像
├── docker-compose.yaml           # 服务编排配置
├── .env                          # 环境变量
└── jar_files/
    └── gcs-connector-hadoop3-2.2.5.jar  # GCS 连接器
```

### 2. 配置文件详解

#### 2.1 cluster-base.Dockerfile
**目的**：提供统一的基础环境（Java 17 + Python 3）

```dockerfile
ARG java_image_tag=17-jre
FROM eclipse-temurin:${java_image_tag}

ARG shared_workspace=/opt/workspace

RUN mkdir -p ${shared_workspace} && \
    apt-get update -y && \
    apt-get install -y python3 && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    rm -rf /var/lib/apt/lists/*

ENV SHARED_WORKSPACE=${shared_workspace}
ENV JAVA_HOME=/opt/java/openjdk
ENV PATH=${JAVA_HOME}/bin:${PATH}
```

**关键配置**：
- `java_image_tag=17-jre`：使用 Java 17（Spark 3.5.0 要求 Java 17）
- `JAVA_HOME` 和 `PATH`：确保 Java 环境正确配置

#### 2.2 spark-base.Dockerfile
**目的**：安装 Apache Spark 并集成 GCS 连接器

```dockerfile
FROM cluster-base

ARG spark_version=3.5.0
ARG hadoop_version=3

RUN apt-get update -y && \
    apt-get install -y curl && \
    curl https://archive.apache.org/dist/spark/spark-${spark_version}/spark-${spark_version}-bin-hadoop${hadoop_version}.tgz -o spark.tgz && \
    tar -xf spark.tgz && \
    mv spark-${spark_version}-bin-hadoop${hadoop_version} /usr/bin/ && \
    mkdir /usr/bin/spark-${spark_version}-bin-hadoop${hadoop_version}/logs && \
    rm spark.tgz

ENV SPARK_HOME /usr/bin/spark-${spark_version}-bin-hadoop${hadoop_version}
ENV SPARK_MASTER_HOST spark-master
ENV SPARK_MASTER_PORT 7077
ENV PYSPARK_PYTHON python3

# 复制 GCS 连接器 JAR 到 Spark jars 目录
COPY jar_files/gcs-connector-hadoop3-2.2.5.jar ${SPARK_HOME}/jars/
```

**关键配置**：
- `spark_version=3.5.0`：使用 Spark 3.5.0
- `GCS 连接器`：支持 `gs://` 协议读写 Google Cloud Storage

#### 2.3 jupyterlab.Dockerfile
**目的**：创建带有 PySpark 和 JupyterLab 的开发环境

```dockerfile
FROM cluster-base

ARG spark_version=3.5.0
ARG jupyterlab_version=3.6.1

RUN apt-get update -y && \
    apt-get install -y python3-pip && \
    pip3 install --break-system-packages wget pyspark==${spark_version} jupyterlab==${jupyterlab_version}

# 复制 GCS 连接器 JAR 到 PySpark jars 目录，支持 gs:// 读写
COPY jar_files/gcs-connector-hadoop3-2.2.5.jar /usr/local/lib/python3.12/dist-packages/pyspark/jars/

EXPOSE 8888
WORKDIR ${SHARED_WORKSPACE}
CMD jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --NotebookApp.token=
```

**关键配置**：
- PySpark 版本与 Spark 版本一致（3.5.0）
- GCS 连接器同时复制到 PySpark 的 jars 目录
- 工作目录挂载到 `/opt/workspace`

#### 2.4 docker-compose.yaml
**目的**：编排多容器服务

```yaml
version: "3.6"

volumes:
  spark-logs:
    driver: local

networks:
  default:
    name: ${PROJECT_NAME}-network
    external: true

services:
  jupyterlab:
    build:
      context: .
      dockerfile: jupyterlab.Dockerfile
    image: supply-chain-jupyterlab
    container_name: ${PROJECT_NAME}-jupyterlab
    volumes:
      - /Users/liceline/.../supply_chain_de_study:/opt/workspace
    environment:
      - PROJECT_ROOT=/opt/workspace
      - GOOGLE_APPLICATION_CREDENTIALS=/opt/workspace/keys/gcp-cred.json
      - GCP_PROJECT_ID=stellar-stream-485314-p0
      - GCS_BUCKET=supply-chain-data-bucket-485314
    ports:
      - 8888:8888

  spark-master:
    build:
      context: .
      dockerfile: spark-master.Dockerfile
    image: supply-chain-spark-master
    container_name: ${PROJECT_NAME}-spark-master
    volumes:
      - /Users/liceline/.../supply_chain_de_study:/opt/workspace
      - spark-logs:/opt/spark-logs
    environment:
      SPARK_LOCAL_IP: spark-master
      PROJECT_ROOT: /opt/workspace
      GOOGLE_APPLICATION_CREDENTIALS: /opt/workspace/keys/gcp-cred.json
    ports:
      - 18080:8080  # Spark Master Web UI（改为 18080 避免端口冲突）
      - 7077:7077   # Spark Master Port

  spark-worker-1:
    build:
      context: .
      dockerfile: spark-worker.Dockerfile
    image: supply-chain-spark-worker
    container_name: ${PROJECT_NAME}-spark-worker-1
    depends_on:
      - spark-master
    volumes:
      - /Users/liceline/.../supply_chain_de_study:/opt/workspace
      - spark-logs:/opt/spark-logs
    environment:
      - SPARK_WORKER_CORES=2
      - SPARK_WORKER_MEMORY=4g
      - GOOGLE_APPLICATION_CREDENTIALS=/opt/workspace/keys/gcp-cred.json
    ports:
      - 8083:8081
```

**关键配置**：
- **外部网络**：`supply-chain-network`（需要预先创建）
- **卷挂载**：本地项目目录挂载到容器 `/opt/workspace`
- **GCP 凭证**：通过环境变量和卷挂载传递
- **端口映射**：
  - `8888`：JupyterLab
  - `18080`：Spark Master Web UI
  - `7077`：Spark Master 服务端口
  - `8083`：Spark Worker Web UI

---

## 执行步骤详解

### 步骤 1：创建 Docker 网络
```bash
docker network create supply-chain-network
```

**目的**：创建供所有容器使用的外部网络

---

### 步骤 2：构建 Docker 镜像
```bash
cd /path/to/docker/spark

docker compose \
  -f docker-compose.yaml \
  --env-file .env \
  build
```

**构建顺序**：
1. `cluster-base`：基础镜像（Java 17 + Python）
2. `spark-base`：Spark 基础镜像 + GCS 连接器
3. `spark-master`、`spark-worker-1`：继承自 spark-base
4. `jupyterlab`：继承自 cluster-base，独立安装 PySpark

**预计时间**：5-10 分钟

---

### 步骤 3：启动容器集群
```bash
docker compose \
  -f docker-compose.yaml \
  --env-file .env \
  up -d
```

**启动顺序**：
1. `jupyterlab`
2. `spark-master`
3. `spark-worker-1`（依赖 spark-master）

**验证启动**：
```bash
docker ps
# 应该看到 3 个容器都在运行

# 访问 Spark Master Web UI
open http://localhost:18080
```

---

### 步骤 4：运行 Batch Pipeline

#### 4.1 Pipeline 代码关键配置

**文件**：`batch_pipeline/data_modeling/transformed_data.py`

```python
# Spark Session 配置
spark = SparkSession.builder \
    .appName('supply-chain-batch-pipeline') \
    .config("spark.jars", jar_file_path) \
    .config("spark.hadoop.fs.AbstractFileSystem.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFS") \
    .config("spark.hadoop.fs.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem") \
    .config("spark.hadoop.google.cloud.auth.service.account.enable", "true") \
    .config("spark.hadoop.google.cloud.auth.service.account.json.keyfile", credentials_path) \
    .config("spark.hadoop.google.cloud.project.id", GCP_PROJECT_ID) \
    .getOrCreate()
```

**关键点**：
- GCS 文件系统实现类必须在 SparkSession 创建**之前**配置
- 服务账号认证文件路径必须正确

#### 4.2 执行命令
```bash
docker exec supply-chain-jupyterlab \
  python /opt/workspace/batch_pipeline/data_modeling/transformed_data.py
```

#### 4.3 执行流程
1. **初始化 SparkSession**（30秒）
   - 加载 GCS 连接器 JAR
   - 配置 Hadoop GCS 文件系统
   - 建立与 GCP 的认证连接

2. **读取 GCS 数据**（10-20 分钟）
   - 路径：`gs://supply-chain-data-bucket-485314/raw_streaming/*.parquet`
   - Stage 2-4：读取并解析 Parquet 文件

3. **数据转换**（5-10 分钟）
   - 创建 7 个维度表：
     - `customer_dimension`
     - `product_dimension`
     - `location_dimension`
     - `order_fact`
     - `shipping_dimension`
     - `department_dimension`
     - `metadata_dimension`

4. **写入 GCS**（20-30 分钟）
   - 路径：`gs://supply-chain-data-bucket-485314/transformed_data/`
   - Stage 5-8：并行写入 Parquet 文件
   - 压缩格式：Snappy

**总耗时**：约 35-60 分钟

---

## 性能优化建议

### 1. 增加并行度

#### 1.1 增加 Spark Worker 数量
**当前配置**：1 个 Worker，2 cores，4GB 内存

**优化方案**：在 `docker-compose.yaml` 添加更多 Worker

```yaml
spark-worker-2:
  build:
    context: .
    dockerfile: spark-worker.Dockerfile
  image: supply-chain-spark-worker
  container_name: ${PROJECT_NAME}-spark-worker-2
  depends_on:
    - spark-master
  volumes:
    - /Users/liceline/.../supply_chain_de_study:/opt/workspace
  environment:
    - SPARK_WORKER_CORES=2
    - SPARK_WORKER_MEMORY=4g
  ports:
    - 8084:8081
```

**预期提升**：读写速度提升 30-50%

---

#### 1.2 调整分区数量
**当前配置**：`config.py` 中 `partition_count = 4`

**优化方案**：
```python
# config.py
partition_count = 8  # 增加到 8 或更多

# 或根据数据量动态调整
# 推荐：partition_count = worker_count * cores_per_worker * 2
# 例如：2 workers * 2 cores * 2 = 8
```

**修改代码**：
```python
# transformed_data.py
def write_to_gcs(dataframes, output_path):
    for name, dataframe in dataframes.items():
        output_file = output_path + name
        # 增加分区数以提高并行写入
        target_df = dataframe.repartition(partition_count)
        target_df.write.mode("overwrite").option("compression", "snappy").parquet(output_file)
```

**预期提升**：写入速度提升 20-40%

---

### 2. 优化 Spark 配置

#### 2.1 在 SparkSession 中添加性能配置
```python
spark = SparkSession.builder \
    .appName('supply-chain-batch-pipeline') \
    .config("spark.jars", jar_file_path) \
    .config("spark.hadoop.fs.AbstractFileSystem.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFS") \
    .config("spark.hadoop.fs.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem") \
    .config("spark.hadoop.google.cloud.auth.service.account.enable", "true") \
    .config("spark.hadoop.google.cloud.auth.service.account.json.keyfile", credentials_path) \
    .config("spark.hadoop.google.cloud.project.id", GCP_PROJECT_ID) \
    # 性能优化配置
    .config("spark.sql.shuffle.partitions", "200")  # 默认 200，可根据数据量调整
    .config("spark.default.parallelism", "16")      # 默认并行任务数
    .config("spark.sql.adaptive.enabled", "true")   # 启用自适应查询执行
    .config("spark.sql.adaptive.coalescePartitions.enabled", "true")  # 自动合并小分区
    .config("spark.executor.memory", "4g")          # Executor 内存
    .config("spark.driver.memory", "2g")            # Driver 内存
    .config("spark.memory.fraction", "0.8")         # JVM 堆内存的 80% 用于 Spark
    .getOrCreate()
```

---

#### 2.2 GCS 连接器优化
```python
# 在 Hadoop 配置中添加 GCS 缓冲区设置
hadoop_conf = spark._jsc.hadoopConfiguration()
hadoop_conf.set("fs.AbstractFileSystem.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFS")
hadoop_conf.set("fs.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem")
hadoop_conf.set("fs.gs.auth.service.account.json.keyfile", credentials_path)
hadoop_conf.set("fs.gs.auth.service.account.enable", "true")

# 性能优化
hadoop_conf.set("fs.gs.block.size", "134217728")  # 128 MB block size
hadoop_conf.set("fs.gs.inputstream.buffer.size", "8388608")  # 8 MB 读取缓冲区
hadoop_conf.set("fs.gs.outputstream.buffer.size", "8388608")  # 8 MB 写入缓冲区
hadoop_conf.set("fs.gs.outputstream.upload.chunk.size", "67108864")  # 64 MB 上传块大小
```

**预期提升**：GCS 读写速度提升 15-25%

---

### 3. 数据读取优化

#### 3.1 启用列裁剪（Column Pruning）
**当前实现**：已经使用列选择

```python
def extract_columns(df, columns_to_extract):
    available_cols = [col_name for col_name in columns_to_extract if col_name in df.columns]
    return df.select(*available_cols)  # ✅ 只读取需要的列
```

**进一步优化**：在读取时就指定列
```python
# 如果知道所有需要的列，可以在读取时指定
all_required_columns = list(set(
    customer_columns + product_columns + location_columns + 
    order_columns + shipping_columns + department_columns + metadata_columns
))

df_raw = spark.read.parquet(input_path + '*').select(*all_required_columns)
```

---

#### 3.2 启用谓词下推（Predicate Pushdown）
如果只需要部分数据，在读取时过滤：

```python
# 例如：只处理特定日期范围的数据
df_raw = spark.read.parquet(input_path + '*') \
    .filter(col("Order date") >= "2020-01-01") \
    .filter(col("Order date") <= "2023-12-31")
```

---

### 4. 写入优化

#### 4.1 避免 `coalesce(1)`
**问题**：`coalesce(1)` 会强制所有数据写入单个文件，造成瓶颈

**当前实现**：✅ 已优化
```python
# 使用 repartition 而不是 coalesce(1)
target_df = dataframe.repartition(partition_count)
target_df.write.mode("overwrite").option("compression", "snappy").parquet(output_file)
```

---

#### 4.2 调整压缩算法
**当前**：Snappy（快速但压缩率低）

**可选方案**：
- `gzip`：高压缩率，慢速（节省存储成本）
- `lz4`：平衡
- `zstd`：高压缩率，较快（推荐）

```python
dataframe.write.mode("overwrite").option("compression", "zstd").parquet(output_file)
```

---

### 5. 资源配置优化

#### 5.1 增加 Worker 内存和 CPU
**当前配置**：
```yaml
environment:
  - SPARK_WORKER_CORES=2
  - SPARK_WORKER_MEMORY=4g
```

**推荐配置**（如果硬件允许）：
```yaml
environment:
  - SPARK_WORKER_CORES=4      # 增加到 4 核
  - SPARK_WORKER_MEMORY=8g    # 增加到 8GB
```

---

#### 5.2 Docker 资源限制
确保 Docker Desktop 有足够资源：
- **CPU**：至少 4 核
- **内存**：至少 8GB
- **磁盘**：至少 20GB

**设置路径**：Docker Desktop → Preferences → Resources

---

### 6. 使用 Cloud Dataproc（生产环境）

对于大规模数据处理，考虑使用 Google Cloud Dataproc：

```bash
# 创建 Dataproc 集群
gcloud dataproc clusters create supply-chain-cluster \
  --region=europe-west4 \
  --zone=europe-west4-a \
  --master-machine-type=n1-standard-4 \
  --master-boot-disk-size=50GB \
  --num-workers=3 \
  --worker-machine-type=n1-standard-4 \
  --worker-boot-disk-size=50GB \
  --image-version=2.1-debian11 \
  --project=stellar-stream-485314-p0

# 提交作业
gcloud dataproc jobs submit pyspark \
  /opt/workspace/batch_pipeline/data_modeling/transformed_data.py \
  --cluster=supply-chain-cluster \
  --region=europe-west4
```

**预期提升**：处理时间从 1 小时缩短到 10-15 分钟

---

## 性能优化总结

| 优化方案 | 难度 | 预期提升 | 成本 |
|---------|------|---------|------|
| 增加 Spark Worker 数量 | 简单 | 30-50% | 本地资源 |
| 调整分区数量 | 简单 | 20-40% | 无 |
| 优化 Spark 配置 | 中等 | 15-25% | 无 |
| 优化 GCS 连接器配置 | 简单 | 15-25% | 无 |
| 增加 Worker 资源 | 简单 | 20-30% | 本地资源 |
| 使用 Cloud Dataproc | 复杂 | 80-90% | GCP 费用 |

**建议优先级**：
1. ✅ 调整分区数量（已实现）
2. 增加 Spark Worker 数量（1 → 2-3）
3. 优化 Spark 和 GCS 配置
4. 增加 Worker 资源（2 cores → 4 cores，4GB → 8GB）
5. 考虑使用 Cloud Dataproc（生产环境）

**综合优化后预期**：
- 当前：60 分钟
- 优化后：15-25 分钟
- Dataproc：10-15 分钟

---

## 常见问题排查

### 问题 1：FileNotFoundException: gs://.../* 不存在
**原因**：GCS 路径为空或不存在

**排查**：
```bash
# 验证 GCS 路径
gsutil ls gs://supply-chain-data-bucket-485314/raw_streaming/

# 检查服务账号权限
gcloud projects get-iam-policy stellar-stream-485314-p0
```

**解决**：
- 确保流处理 Pipeline 已生成数据
- 验证服务账号有 `roles/storage.objectViewer` 权限

---

### 问题 2：Java version mismatch
**错误**：`UnsupportedClassVersionError: class file version 61.0`

**原因**：Java 版本过低（需要 Java 17）

**解决**：
```dockerfile
# cluster-base.Dockerfile 中指定 Java 17
ARG java_image_tag=17-jre
FROM eclipse-temurin:${java_image_tag}
```

---

### 问题 3：Wrong FS: gs://, expected: file:///
**原因**：GCS 文件系统未正确配置

**解决**：
1. 确保 GCS 连接器 JAR 已复制到 Spark jars 目录
2. 在 SparkSession 配置中添加 GCS 文件系统实现
3. 使用 `path.getFileSystem(hadoop_conf)` 而不是 `FileSystem.get(hadoop_conf)`

---

### 问题 4：Port already allocated (8080)
**原因**：端口 8080 被占用

**解决**：
```yaml
# docker-compose.yaml 修改端口映射
ports:
  - 18080:8080  # 使用其他端口
```

---

### 问题 5：Pipeline 卡在某个 Stage
**排查**：
```bash
# 查看 Spark Master UI
open http://localhost:18080

# 查看容器日志
docker logs supply-chain-jupyterlab
docker logs supply-chain-spark-master
docker logs supply-chain-spark-worker-1

# 查看 Spark 任务详情
docker exec supply-chain-spark-master cat /opt/spark-logs/spark-master.out
```

**常见原因**：
- Worker 资源不足
- 网络 I/O 瓶颈（GCS 读写）
- 分区数量不合理

---

## 附录：完整执行脚本

创建一键执行脚本 `run_batch_pipeline.sh`：

```bash
#!/bin/bash
set -e

PROJECT_ROOT="/Users/liceline/Documents/study_material/data_engineer/project_study/supply_chain/supply_chain_de_study"
DOCKER_SPARK_DIR="$PROJECT_ROOT/docker/spark"

echo "🚀 Starting Batch Pipeline Execution..."

# 1. 创建 Docker 网络（如果不存在）
echo "📡 Creating Docker network..."
docker network create supply-chain-network 2>/dev/null || echo "Network already exists"

# 2. 构建 Docker 镜像
echo "🔨 Building Docker images..."
cd "$DOCKER_SPARK_DIR"
docker compose -f docker-compose.yaml --env-file .env build

# 3. 启动容器
echo "🐳 Starting Docker containers..."
docker compose -f docker-compose.yaml --env-file .env up -d

# 4. 等待服务启动
echo "⏳ Waiting for services to start..."
sleep 10

# 5. 验证服务状态
echo "✅ Checking service status..."
docker ps --filter "name=supply-chain"

# 6. 运行 Batch Pipeline
echo "🎯 Running Batch Pipeline..."
docker exec supply-chain-jupyterlab \
  python /opt/workspace/batch_pipeline/data_modeling/transformed_data.py

echo "🎉 Batch Pipeline execution completed!"
```

**使用方法**：
```bash
chmod +x run_batch_pipeline.sh
./run_batch_pipeline.sh
```

---

## 总结

### 关键配置要点
1. **Java 17**：Spark 3.5.0 的必要条件
2. **GCS 连接器**：同时复制到 Spark 和 PySpark 的 jars 目录
3. **GCS 文件系统配置**：在 SparkSession 创建前配置
4. **分区策略**：避免 `coalesce(1)`，使用合理的 `repartition`
5. **资源配置**：根据数据量调整 Worker 数量和资源

### 性能提升路径
- **短期**（本地开发）：增加 Worker、优化配置 → 15-25 分钟
- **长期**（生产环境）：迁移到 Cloud Dataproc → 10-15 分钟

### 监控与调试
- Spark Master UI: http://localhost:18080
- JupyterLab: http://localhost:8888
- 日志：`docker logs <container_name>`

---

**文档版本**：v1.0  
**最后更新**：2026-02-05  
**作者**：Supply Chain Data Platform Team
