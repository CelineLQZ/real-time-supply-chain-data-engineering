# 🚀 Supply Chain Data Platform - Terraform 完整指南

## 📋 目录

1. [快速开始](#快速开始)
2. [文件说明](#文件说明)
3. [部署步骤](#部署步骤)
4. [资源概览](#资源概览)
5. [ADC 认证](#adc-认证)
6. [常见问题](#常见问题)

---

## 🚀 快速开始

### 前置要求检查

```bash
# 1. 进入 terraform 目录
cd /Users/liceline/Documents/study_material/data_engineer/project_study/supply_chain/supply_chain_de_study/terraform

# 2. 检查所需工具
terraform version    # 需要 >= 1.0
gcloud --version     # 需要安装 gcloud

# 3. 设置 ADC 认证
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/../keys/gcp-cred.json"

# 4. 验证认证
gcloud auth list
gcloud config get-value project
```

### 一键部署（推荐）

```bash
# 使用自动化脚本
chmod +x deploy.sh
./deploy.sh
```

### 手动部署步骤

```bash
# 1️⃣ 初始化
terraform init

# 2️⃣ 验证配置
terraform validate

# 3️⃣ 查看计划
terraform plan

# 4️⃣ 应用配置
terraform apply

# 5️⃣ 查看结果
terraform output
```

---

## 📁 文件说明

### 核心文件

| 文件 | 说明 | 修改频率 |
|------|------|--------|
| **main.tf** | 所有资源定义（GCS、BigQuery、SQL、CE） | 低 |
| **variables.tf** | 变量声明和默认值 | 低 |
| **outputs.tf** | 输出定义 | 很低 |
| **terraform.tfvars** | 环境特定的变量值 | 高 |
| **deploy.sh** | 自动部署脚本 | 很低 |

### 辅助文件

```
terraform/
├── .terraform/              # Terraform 缓存（不提交）
├── .terraform.lock.hcl      # 依赖锁定（可选提交）
├── .gitignore               # Git 忽略配置
├── terraform.tfstate        # 状态文件（不提交）
├── terraform.tfstate.backup # 状态备份（不提交）
└── scripts/
    └── spark-startup.sh     # Spark 启动脚本
```

---

## 🔧 部署步骤

### 步骤 1：环境验证

```bash
# 检查 GCP 项目
gcloud projects describe stellar-stream-485314-p0

# 列出你的角色
gcloud projects get-iam-policy stellar-stream-485314-p0 \
  --flatten="bindings[].members" \
  --filter="bindings.members:$(gcloud config get-value account)"
```

### 步骤 2：自定义配置

编辑 `terraform.tfvars`，修改以下内容（如需要）：

```hcl
# 必须修改
project_id                = "stellar-stream-485314-p0"

# 可选修改
region                    = "us-central1"
machine_type              = "n1-standard-4"
cloudsql_root_password    = "YourPassword123!"

# 禁用某些服务
enable_compute_engine     = true   # 改为 false 不创建 Spark 集群
enable_cloudsql           = true   # 改为 false 不创建 Cloud SQL
```

### 步骤 3：执行部署

```bash
# 方式 A：使用脚本（推荐）
./deploy.sh

# 方式 B：手动执行
terraform init
terraform plan
terraform apply
```

### 步骤 4：验证部署

```bash
# 查看所有输出信息
terraform output

# 或查看特定资源
terraform output service_account_email
terraform output spark_cluster_ssh_command
```

---

## 📊 资源概览

### 架构图

```
┌─────────────────────────────────────────────────────────┐
│                GCP Project                              │
│           stellar-stream-485314-p0                       │
└─────────────────────────────────────────────────────────┘
           │
    ┌──────┴──────┬───────────┬──────────┬────────────┐
    │             │           │          │            │
    ↓             ↓           ↓          ↓            ↓
┌────────────┐ ┌────────┐ ┌──────────┐ ┌──────────┐ ┌──────┐
│   GCS      │ │BigQuery│ │Cloud SQL │ │Compute   │ │ IAM  │
│ Buckets    │ │Datasets│ │PostgreSQL│ │ Engine   │ │  &   │
└────────────┘ └────────┘ └──────────┘ └──────────┘ │ Sec. │
  2 Buckets    3 Datasets  1 Instance  1 Instance  └──────┘
  - raw-data   - Bronze    - metadata  - Spark
  - transformed - Silver   - DB        - Cluster
               - Gold
```

### 资源清单

#### GCS 存储桶（2 个）

```
📦 supply-chain-raw-data
   ├── 用途：存储原始数据（CSV、Kafka）
   ├── 版本控制：启用
   └── 保留策略：30 天自动删除

📦 supply-chain-transformed-data
   ├── 用途：存储 Spark 转换后的数据
   ├── 版本控制：启用
   └── 保留策略：30 天自动删除
```

#### BigQuery 数据集（3 个）

```
🗄️ supply_chain_bronze （原始层）
   └── raw_orders（原始订单表）

🗄️ supply_chain_silver （清洗层）
   └── dim_customer（客户维度表）

🗄️ supply_chain_gold （业务层）
   └── kpi_metrics（KPI 指标表）
```

#### Service Account

```
👤 supply-chain-data-pipeline
   ├── 权限：
   │   ├── GCS Admin（两个 bucket）
   │   ├── BigQuery Admin
   │   ├── Compute Admin
   │   └── Cloud SQL Client
   └── 邮箱：supply-chain-data-pipeline@stellar-stream-485314-p0.iam.gserviceaccount.com
```

#### Cloud SQL

```
🗄️ supply-chain-metadata-db
   ├── 类型：PostgreSQL 15
   ├── 机型：db-f1-micro
   ├── 数据库：supply_chain_metadata
   ├── 用户：postgres, supply_chain_app
   └── 备份：启用
```

#### Compute Engine

```
💻 supply-chain-spark-cluster
   ├── 机器类型：n1-standard-4 (4vCPU, 15GB)
   ├── 操作系统：Debian 11
   ├── 预装软件：
   │   ├── Java 11
   │   ├── Python 3
   │   └── Spark 3.4.0
   ├── Service Account：supply-chain-data-pipeline
   └── 启动脚本：scripts/spark-startup.sh
```

---

## 🔐 ADC 认证

### 什么是 ADC？

**Application Default Credentials (应用默认凭证)**

- ✅ 无需存储密钥文件
- ✅ 凭证自动轮换
- ✅ 符合 Google 官方推荐
- ✅ 支持本地开发和生产环境

### 三个认证源（按优先级）

```
1️⃣ 环境变量 GOOGLE_APPLICATION_CREDENTIALS
   ↓
2️⃣ gcloud CLI 本地缓存凭证
   ↓
3️⃣ GCP 资源默认服务账户
```

### 设置 ADC

#### 方式 A：使用凭证文件（推荐用于本地开发）

```bash
# 1. 确保凭证文件存在
ls -la keys/gcp-cred.json

# 2. 设置环境变量
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/keys/gcp-cred.json"

# 3. 验证
echo $GOOGLE_APPLICATION_CREDENTIALS
```

#### 方式 B：使用 gcloud CLI（推荐用于完全本地开发）

```bash
# 1. 登录
gcloud auth login

# 2. 设置项目
gcloud config set project stellar-stream-485314-p0

# 3. 获取应用默认凭证
gcloud auth application-default login

# 现在无需设置环境变量，SDK 会自动使用 gcloud 的凭证
```

### 在 .env 中配置

创建 `.env` 文件（位于 supply_chain_de_study 根目录）：

```bash
GOOGLE_APPLICATION_CREDENTIALS="./keys/gcp-cred.json"
GCP_PROJECT_ID="stellar-stream-485314-p0"
PYTHONPATH=".:./streaming_pipeline"
```

然后在脚本中加载：

```python
from dotenv import load_dotenv
import os

load_dotenv()
project_id = os.getenv('GCP_PROJECT_ID')
```

---

## 📝 常用命令

### 查看资源状态

```bash
# 列出所有资源
terraform state list

# 查看特定资源详情
terraform state show google_storage_bucket.raw_data

# 刷新状态
terraform refresh
```

### 修改资源

```bash
# 修改某个变量
terraform apply -var="machine_type=n1-standard-8"

# 只更新特定资源
terraform apply -target=google_compute_instance.spark_cluster

# 销毁特定资源
terraform destroy -target=google_storage_bucket.raw_data
```

### 导入现有资源

```bash
# 如果资源已存在，导入到 Terraform 管理
terraform import google_storage_bucket.raw_data supply-chain-raw-data
```

### 格式化和验证

```bash
terraform fmt                      # 格式化代码
terraform fmt -recursive           # 递归格式化
terraform validate                 # 验证语法
terraform plan -json | jq .        # JSON 格式查看计划
```

---

## 🚨 常见问题

### Q1: "错误：找不到凭证"

**解决**：
```bash
# 检查环境变量
echo $GOOGLE_APPLICATION_CREDENTIALS

# 重新设置
export GOOGLE_APPLICATION_CREDENTIALS="./keys/gcp-cred.json"

# 或使用 gcloud
gcloud auth application-default login
```

### Q2: "权限不足"

**解决**：
```bash
# 检查你的角色
gcloud projects get-iam-policy stellar-stream-485314-p0 \
  --flatten="bindings[].members"

# 添加 Editor 角色
gcloud projects add-iam-policy-binding stellar-stream-485314-p0 \
  --member="user:$(gcloud config get-value account)" \
  --role="roles/editor"
```

### Q3: "资源已存在"

**解决**：
```bash
# 选项 1：导入现有资源
terraform import google_storage_bucket.raw_data supply-chain-raw-data

# 选项 2：删除并重新创建
terraform destroy -target=google_storage_bucket.raw_data
terraform apply
```

### Q4: "如何销毁所有资源"

**解决**：
```bash
# 查看将删除的资源
terraform plan -destroy

# 确认后销毁
terraform destroy
```

### Q5: "如何备份状态文件"

**解决**：
```bash
# 手动备份
cp terraform.tfstate terraform.tfstate.backup

# 或使用远程状态（GCS）
# 在 backend.tf 中配置
```

---

## 📚 相关资源

- [Terraform 官方文档](https://www.terraform.io/docs)
- [Google Provider 文档](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [GCP 最佳实践](https://cloud.google.com/docs/terraform/best-practices)
- [ADC 文档](https://cloud.google.com/docs/authentication/application-default-credentials)

---

## ✅ 部署检查清单

- [ ] Terraform 版本 >= 1.0
- [ ] gcloud CLI 已安装
- [ ] 凭证文件存在：`keys/gcp-cred.json`
- [ ] 环境变量已设置：`GOOGLE_APPLICATION_CREDENTIALS`
- [ ] 项目 ID 正确：`stellar-stream-485314-p0`
- [ ] `terraform.tfvars` 已修改
- [ ] `terraform validate` 通过
- [ ] `terraform plan` 显示正确的资源
- [ ] 确认部署（执行 `terraform apply`）
- [ ] 所有输出都显示成功
- [ ] 验证资源已创建：`gsutil ls`, `bq ls` 等

---

## 🎯 下一步

1. **运行部署**
   ```bash
   ./deploy.sh
   ```

2. **验证资源**
   ```bash
   gsutil ls
   bq ls
   gcloud compute instances list
   gcloud sql instances list
   ```

3. **连接到 Spark 集群**
   ```bash
   $(terraform output -raw spark_cluster_ssh_command)
   ```

4. **配置 Python/Spark 应用**
   - 使用 `terraform output service_account_email`
   - 在应用中配置 GCS 和 BigQuery 连接

5. **阅读具体文档**
   - `terraform/README.md` - Terraform 详细文档
   - `../README.md` - 项目主文档

---

**最后更新**：2026-01-24
**版本**：1.0
