# Kafka 流处理 Demo - 供应链数据

一个轻量级的 Kafka 流处理项目，用于学习 Kafka 核心概念和与 GCS 的集成。



## 项目结构

```
streaming_pipeline/
├── kafka_config.py       # 统一配置文件
├── producer.py           # 数据生产者
├── consumer.py           # 数据消费者
├── requirements.txt      # Python 依赖
└── README.md            # 本文档
```

## 配置说明

### Kafka 配置
- **KAFKA_BOOTSTRAP_SERVERS**: `localhost:9092` (宿主机访问)
- **KAFKA_TOPIC**: Topic 名称，会自动创建
- **BATCH_SIZE**: Producer 每批发送的记录数
- **SEND_INTERVAL**: 批次间隔，模拟流式场景

### GCS 配置
- **GCS_BUCKET_NAME**: 目标 bucket（需提前创建）
- **GCS_CREDENTIALS_PATH**: 服务账号 JSON 文件路径
- **GCS_OUTPUT_PREFIX**: 输出文件的路径前缀

### Consumer 配置
- **CONSUMER_GROUP_ID**: Consumer Group ID
- **AUTO_OFFSET_RESET**: `earliest` (从头消费) 或 `latest` (只消费新消息)
- **buffer_size**: 内存缓冲区大小（条记录）

## 使用场景

### 场景 1: 完整流程测试
```bash
# Terminal 1: 启动 Consumer (先启动，等待消息)
python consumer.py

# Terminal 2: 启动 Producer (发送数据)
python producer.py
```

### 场景 2: 重新消费数据
```bash
# 修改 kafka_config.py 中的 CONSUMER_GROUP_ID
CONSUMER_GROUP_ID = 'new-consumer-group'

# 重新运行 consumer
python consumer.py
```

### 场景 3: 调整发送速度
```bash
# 编辑 kafka_config.py
BATCH_SIZE = 50       # 增大批次
SEND_INTERVAL = 0.5   # 缩短间隔

# 重新运行 producer
python producer.py
```

## 监控和调试

### 查看 Kafka Topic
访问 Control Center: http://localhost:9021
- Topics → supply-chain-orders
- 查看消息数量、分区、消费者状态

### 查看 Kafka 日志
```bash
cd docker/kafka
docker-compose logs -f kafka
```

## 🔍 读取 GCS Bucket 中的数据

### 方法 1: 使用 Python（推荐）

创建 `read_gcs.py` 文件：

```python
from google.cloud import storage
import json
import os

# 设置认证
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '../keys/gcp-cred.json'

# 初始化 GCS 客户端
client = storage.Client()
bucket_name = 'your-bucket-name'  # 修改为你的 bucket
bucket = client.bucket(bucket_name)

# 列出所有文件
print("📁 Bucket 中的文件：")
blobs = list(bucket.list_blobs(prefix='streaming_data/supply_chain/'))
for blob in blobs:
    print(f"  - {blob.name} ({blob.size} bytes, {blob.time_created})")

# 读取最新的 JSON 文件
if blobs:
    latest_blob = sorted(blobs, key=lambda x: x.time_created)[-1]
    
    print(f"\n📄 读取文件: {latest_blob.name}")
    content = latest_blob.download_as_string()
    data = json.loads(content)
    
    print(f"\n✅ 读取成功！共 {len(data)} 条记录")
    print("\n前 3 条记录示例：")
    for record in data[:3]:
        print(f"  Order ID: {record.get('Order Id')}")
        print(f"  Customer: {record.get('Customer Fname')} {record.get('Customer Lname')}")
        print(f"  Status: {record.get('Order Status')}")
        print(f"  Sales: ${record.get('Sales')}")
        print()
else:
    print("⚠️  未找到任何文件")
```

运行：
```bash
cd streaming_pipeline
python read_gcs.py
```

### 方法 2: 使用 gsutil 命令行

```bash
# 列出所有文件
gsutil ls gs://your-bucket-name/streaming_data/supply_chain/

# 查看文件详情
gsutil ls -l gs://your-bucket-name/streaming_data/supply_chain/

# 下载文件到本地
gsutil cp gs://your-bucket-name/streaming_data/supply_chain/orders_*.json ./downloaded_data/

# 直接查看文件内容（前 20 行）
gsutil cat gs://your-bucket-name/streaming_data/supply_chain/orders_20260128_*.json | head -20

# 统计文件数量
gsutil ls gs://your-bucket-name/streaming_data/supply_chain/ | wc -l
```

### 方法 3: 在 GCP Console 中查看

1. 打开 [GCP Storage Browser](https://console.cloud.google.com/storage/buckets)
2. 选择你的 bucket
3. 导航到 `streaming_data/supply_chain/` 目录
4. 点击 JSON 文件
5. 可以下载、预览或分享

### 方法 4: 使用 BigQuery 分析（高级）

```bash
# 创建外部表指向 GCS JSON 文件
bq mk --external_table_definition=gs://your-bucket-name/streaming_data/supply_chain/*.json \
  my_dataset.supply_chain_orders

# 查询数据
bq query --use_legacy_sql=false \
  'SELECT * FROM my_dataset.supply_chain_orders LIMIT 10'
```

### 查看 GCS 数据
```bash
gsutil ls gs://your-bucket/streaming_data/supply_chain/
```

### 常见问题

**Q: Producer 连接失败**
- 确保 Docker Desktop 运行
- 检查 Kafka 服务状态: `docker-compose ps`
- 验证端口未被占用: `lsof -i :9092`

**Q: Consumer 无法写入 GCS**
- 检查 `keys/gcp-cred.json` 文件存在
- 确认 bucket 名称正确（在 `kafka_config.py` 中修改）
- 验证服务账号权限（Storage Object Creator）
- 确保 GCP 项目 billing 已启用
- 错误 403：billing 问题
- 错误 404：bucket 不存在

**Q: Consumer 收不到消息**
- 确保 Producer 已运行并发送数据
- 检查 Topic 名称是否一致
- 在 Control Center 中验证消息是否存在

**Q: 如何停止后台运行的 Consumer**
```bash
pkill -f consumer
# 或查看并手动杀死
ps aux | grep consumer
kill <PID>
```

## 清理和重置

### 停止 Python 进程
```bash
# 停止所有 Python 进程
pkill -f python

# 停止特定进程
pkill -f "python consumer.py"
pkill -f "python producer.py"
```

### 停止 Kafka 服务
```bash
cd docker/kafka
docker-compose down
```

### 完全清理（删除数据）
```bash
docker-compose down -v
docker network rm supply-chain-de-network
```

### 重置 Consumer Offset
```bash
# 方法1: 修改 Consumer Group ID（在 kafka_config.py 中）
CONSUMER_GROUP_ID = 'new-consumer-group'

# 方法2: 删除 Consumer Group（在 Control Center 中）
# http://localhost:9021 → Consumers → 删除 Group
```

### 清理 GCS 数据
```bash
# 删除所有流处理输出
gsutil rm -r gs://your-bucket-name/streaming_data/supply_chain/

# 或选择性删除
gsutil rm gs://your-bucket-name/streaming_data/supply_chain/orders_20260128_*.json
```

## 学习要点

通过这个 Demo 你将学习：

1. **Kafka 核心概念**
   - Topic、Partition、Offset
   - Producer/Consumer 模式
   - Consumer Group

2. **流式数据处理**
   - 批量发送和消费
   - 缓冲区管理
   - 容错和重试

3. **与云服务集成**
   - GCS 认证和授权
   - 数据持久化策略
   - 批量写入优化

4. **实际操作技能**
   - Docker Compose 管理
   - Python Kafka 客户端使用
   - 日志监控和调试

## 📝 项目文件结构

```
streaming_pipeline/
├── kafka_config.py       # 统一配置文件（修改 bucket 名称在这里）
├── producer.py           # 数据生产者
├── consumer.py           # 数据消费者
├── read_gcs.py          # （可选）读取 GCS 数据的脚本
├── requirements.txt      # Python 依赖
├── consumer.log         # Consumer 运行日志（自动生成）
└── README.md           # 本文档
```

太好了，你这一段**其实已经是“完整项目复盘”的原材料了**。
我帮你做三件事（一步到位）：

1️⃣ **把你刚才口述的内容，整理成一份结构清晰的中文 Markdown 笔记（可直接放 GitHub）**
2️⃣ **明确回答你最困惑的点：Python 解释器到底选哪一个、怎么“自己判断”**
3️⃣ **把 Kafka / Python / GCS 在这个 demo 里的“各自职责”和运行顺序说清楚**

下面你可以直接复制使用 👇

---

# Kafka + Cloud Storage 数据流 Demo（完整整理笔记）

## 一、项目背景与目标

本项目的目的是：

> 使用 **Kafka** 构建一个简单的数据流（Data Stream Demo），
> 将本地数据通过 **Producer → Kafka → Consumer** 的方式传输，
> 并最终将数据写入 **Google Cloud Storage（GCS）**，
> 用于验证 Kafka 与云端存储服务的集成能力。

---

## 二、Kafka 的来源与运行方式

### 1️⃣ Kafka 的来源（Zogot + 官方镜像）

* 通过 **Zogot / Docker Desktop** 下载并运行 Kafka
* 使用的是 **Confluent 官方 Kafka Docker 镜像**
* Kafka 运行在 **Docker container 中**，不是本地进程，也不是虚拟机

Kafka 相关文件主要包括：

* `docker-compose.yaml`
* `.env`（环境变量文件）

---

### 2️⃣ Kafka Docker 配置说明（有没有“被修改”？）

Kafka 使用的是官方镜像：

* `confluentinc/cp-kafka`
* `confluentinc/cp-zookeeper`

常见需要“关注”的配置点（不算魔改）：

* 端口映射：`9092:9092`
* `KAFKA_ADVERTISED_LISTENERS`
* `KAFKA_ZOOKEEPER_CONNECT`

👉 这些配置**不是你随意改的逻辑**，而是 Kafka 在 Docker 场景下**必须显式配置**的内容。

---

### 3️⃣ Kafka 环境变量文件（.env）

Kafka 在 Docker 中运行时，**依赖环境变量文件**来适配本地环境：

* 不同机器端口不同
* 不同项目 network 名不同
* 不同组件是否启用不同

.env 的作用是：

> 让 Kafka 在“你的本地环境”中可以被正确访问
> （尤其是 `localhost:9092`）

---

## 三、Streaming Pipeline（Python 代码部分）

Kafka 启动后，真正的数据流逻辑在 `streaming_pipeline/` 中。

### 项目结构

```text
streaming_pipeline/
├── requirements.txt        # Python 依赖
├── kafka_config.py         # Kafka + GCS 统一配置
├── producer.py             # Kafka Producer
├── consumer.py             # Kafka Consumer（写入 GCS）
```

---

### 1️⃣ requirements.txt（非常关键）

```txt
kafka-python==2.0.2
google-cloud-storage==2.10.0
```

⚠️ **注意**：
requirements 是否“生效”，完全取决于你用的是**哪个 Python 解释器**。

---

## 四、Python 解释器：你最容易混乱、但最重要的一点

### ❓ 我的疑问：Python 解释器到底该选哪一个？

这是一个**非常专业、也非常真实的问题**。

---

### ✅ 你应该怎么“自己判断”解释器？

在终端中运行：

```bash
which python3
python3 --version
```

你得到的是：

```text
/opt/homebrew/bin/python3
Python 3.13.7
```

这说明：

* 你用的是 **Homebrew 安装的 Python**
* 版本是 **3.13（非常新）**

---

### ❗ 为什么 Python 3.13 会带来问题？

* 很多第三方库（包括 `google-cloud-storage`）
* **还没完全适配 Python 3.13**
* 会出现：安装成功但 import 失败 / 行为异常

👉 **这不是你写错，是生态没跟上**

---

### ✅ 推荐你在这个项目中使用的解释器版本

> **Python 3.11（最稳妥、最通用）**

原因：

* GCP SDK 官方长期支持
* Kafka / Data 工具生态稳定
* 实际工程和实习中最常见

---

### 🔧 如何在 VS Code 中选对解释器（非常重要）

1. 打开 VS Code（项目根目录）
2. 按下：

```text
Cmd + Shift + P
```

3. 输入并选择：

```text
Python: Select Interpreter
```

4. 选择：

```text
/opt/homebrew/bin/python3.11
```

（如果没有，先用 `brew install python@3.11` 安装）

👉 从这一刻开始：

* VS Code 运行
* VS Code Terminal
* VS Code Debug

**全部使用同一个 Python**

---

## 五、kafka_config.py：配置里最容易踩的坑

### 1️⃣ GCS Bucket 名称必须是“真实存在的”

```python
GCS_BUCKET_NAME = "your-bucket-name"
```

⚠️ 注意：

* **bucket name 是全局唯一的**
* 很多时候后面会带随机数字
* 一定要去 **Google Cloud Console → Storage** 中复制真实名称

否则：

* 程序可以跑
* 但写入会失败（403 / 404）

---

### 2️⃣ Billing 必须开启（你已经踩过）

* GCS 写入 = **计费操作**
* Project 如果 `Billing is disabled`
* 写入一定 403

👉 这是 **云平台规则，不是代码问题**

---

## 六、如何运行这个 Demo（标准顺序）

### ✅ 正确的运行顺序（非常重要）

#### Step 1：启动 Kafka（Docker）

```bash
cd docker/kafka
docker-compose up -d
```

---

#### Step 2：先启动 Consumer（监听）

```bash
cd streaming_pipeline
python consumer.py
```

目的：

* 建立 Consumer Group
* 准备接收数据

---

#### Step 3：停止 Consumer（Ctrl + C）

这是**正常操作**，不是错误。

---

#### Step 4：运行 Producer（发送数据）

```bash
python producer.py
```

Producer 会把数据发送到 Kafka Topic。

---

#### Step 5：再次启动 Consumer（消费 + 写入）

```bash
python consumer.py
```

此时：

* Consumer 会从 Kafka 读取数据
* 并将数据写入 **Google Cloud Storage Bucket**

---

## 七、整体架构回顾（你在做什么）

```text
本地数据
  ↓
Producer (Python)
  ↓
Kafka (Docker)
  ↓
Consumer (Python)
  ↓
Google Cloud Storage
```

* Kafka：数据缓冲与解耦
* Producer / Consumer：流式处理逻辑
* GCS：最终落库（验证云集成）






