# Supply Chain Data Engineering - CI/CD 策略

## 项目架构概览
```
Kafka (Streaming) → GCS raw_staging → Batch Pipeline → GCS transformed_data
                                            ↓
                                      BigQuery Tables
                                            ↓
                                      dbt Models (Staging + Marts)
                                            ↓
                                   Analytics Dashboard
```

---

## 1. 整体 CI/CD 流程

### 阶段划分
```
Push to GitHub 
    ↓
1️⃣ Code Quality Checks (Linting, Format)
    ↓
2️⃣ Unit Tests (Python, dbt)
    ↓
3️⃣ Integration Tests (Streaming, Batch)
    ↓
4️⃣ Infrastructure Validation (Terraform)
    ↓
5️⃣ Build & Push Artifacts (Docker Images)
    ↓
6️⃣ Deploy to Dev/Staging Environment
    ↓
7️⃣ Production Deployment (Manual Approval)
```

---

## 2. 各组件的 CI/CD 检查清单

### 📍 **Python Code (Streaming + Batch Pipeline)**

#### 检查项目
```bash
# 1. Linting
pylint streaming_pipeline/kafka/*.py
pylint batch_pipeline/data_modeling/*.py

# 2. Code Formatting
black --check streaming_pipeline/ batch_pipeline/

# 3. Type Checking
mypy streaming_pipeline/kafka/ batch_pipeline/

# 4. Security Scanning
bandit -r streaming_pipeline/ batch_pipeline/

# 5. Dependency Scanning
safety check -r streaming_pipeline/kafka/requirements.txt
safety check -r batch_pipeline/data_modeling/requirements.txt
```

#### 单元测试示例
```python
# tests/test_consumer.py
import unittest
from streaming_pipeline.kafka.consumer import KafkaConsumer

class TestKafkaConsumer(unittest.TestCase):
    def test_connection(self):
        """测试 Kafka 连接"""
        consumer = KafkaConsumer()
        self.assertIsNotNone(consumer.client)
    
    def test_message_parsing(self):
        """测试消息解析"""
        message = {"Order_Id": 1, "Order_Date": "01/01/2020 10:00"}
        parsed = consumer.parse_message(message)
        self.assertIn("Order_Id", parsed)
```

---

### 🏗️ **dbt Models**

#### 检查项目
```bash
# 1. dbt Parse Check
dbt parse --profiles-dir dbt

# 2. dbt Compile
dbt compile --profiles-dir dbt

# 3. dbt Test (Data Quality)
dbt test --profiles-dir dbt

# 4. dbt Doc Generation
dbt docs generate --profiles-dir dbt

# 5. dbt Freshness Check
dbt source freshness --profiles-dir dbt
```

#### 必需的 dbt 测试
```yaml
# dbt/models/staging/schema.yaml
models:
  - name: dim_order
    columns:
      - name: order_id
        tests:
          - not_null
          - unique
      - name: order_date
        tests:
          - not_null
      - name: order_item_total
        tests:
          - dbt_expectations.expect_column_values_to_be_of_type:
              column_type: numeric

  - name: fact_order
    tests:
      - dbt_utils.recency:
          datepart: day
          interval: 1
          field: order_date
```

---

### 🏢 **Terraform Infrastructure**

#### 检查项目
```bash
# 1. Terraform Format Check
terraform fmt -check -recursive

# 2. Terraform Validate
terraform validate

# 3. Security Scanning
tfsec

# 4. Cost Estimation
terraform plan -out=tfplan
terraform show tfplan | grep "will be created"
```

#### Terraform 部署步骤
```bash
# 1. Plan
terraform plan -out=tfplan -var-file="prod.tfvars"

# 2. Show Plan (手动审核)
terraform show tfplan

# 3. Apply (需要 approval)
terraform apply tfplan
```

---

### 🐳 **Docker Images**

#### 构建和推送
```bash
# 1. Build Spark Image
docker build -t gcr.io/stellar-stream-485314-p0/spark-base:latest -f docker/spark/spark-base.Dockerfile .

# 2. Push to GCR
docker push gcr.io/stellar-stream-485314-p0/spark-base:latest

# 3. Build Kafka Consumer Image
docker build -t gcr.io/stellar-stream-485314-p0/kafka-consumer:latest \
  -f docker/kafka/Dockerfile .
```

---

## 3. GitHub Actions 工作流配置

### 📋 Main CI Workflow
```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  # Job 1: Code Quality
  code-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install pylint black mypy bandit safety
          pip install -r streaming_pipeline/kafka/requirements.txt
          pip install -r batch_pipeline/data_modeling/requirements.txt
      
      - name: Run Pylint
        run: |
          pylint streaming_pipeline/kafka/*.py
          pylint batch_pipeline/data_modeling/*.py
        continue-on-error: true
      
      - name: Check code format
        run: black --check streaming_pipeline/ batch_pipeline/
      
      - name: Run type check
        run: mypy streaming_pipeline/kafka/ batch_pipeline/
      
      - name: Security check
        run: |
          bandit -r streaming_pipeline/ batch_pipeline/
          safety check

  # Job 2: dbt Validation
  dbt-validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dbt
        run: pip install dbt-bigquery
      
      - name: dbt Parse
        working-directory: dbt
        run: dbt parse --profiles-dir .
      
      - name: dbt Compile
        working-directory: dbt
        run: dbt compile --profiles-dir .

  # Job 3: Terraform Validation
  terraform-validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v2
      
      - name: Terraform Format Check
        run: terraform fmt -check -recursive terraform/
      
      - name: Terraform Validate
        run: terraform validate
        working-directory: terraform/
      
      - name: TFSec Security Scan
        run: |
          pip install tfsec
          tfsec terraform/

  # Job 4: Unit Tests
  unit-tests:
    runs-on: ubuntu-latest
    services:
      kafka:
        image: confluentinc/cp-kafka:latest
        env:
          KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install test dependencies
        run: |
          pip install pytest pytest-cov
          pip install -r streaming_pipeline/kafka/requirements.txt
          pip install -r batch_pipeline/data_modeling/requirements.txt
      
      - name: Run tests
        run: pytest tests/ --cov=streaming_pipeline --cov=batch_pipeline

  # Job 5: Coverage Report
  coverage:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v3
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
```

### 📋 Deployment Workflow (Dev/Staging/Prod)
```yaml
# .github/workflows/deploy.yml
name: Deploy Pipeline

on:
  workflow_dispatch:  # Manual trigger
    inputs:
      environment:
        description: 'Environment to deploy'
        required: true
        default: 'dev'
        type: choice
        options:
          - dev
          - staging
          - prod
      approve:
        description: 'I have reviewed all changes'
        required: true
        type: boolean

env:
  PROJECT_ID: stellar-stream-485314-p0
  GCR_HOSTNAME: gcr.io

jobs:
  deploy-infrastructure:
    runs-on: ubuntu-latest
    environment: ${{ github.event.inputs.environment }}
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v2
      
      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      
      - name: Terraform Plan
        working-directory: terraform/
        run: |
          terraform init -backend-config="bucket=supply-chain-tf-state-${{ github.event.inputs.environment }}"
          terraform plan -out=tfplan -var-file="${{ github.event.inputs.environment }}.tfvars"
      
      - name: Terraform Apply
        working-directory: terraform/
        if: github.event.inputs.approve == 'true'
        run: terraform apply tfplan

  build-docker-images:
    runs-on: ubuntu-latest
    needs: deploy-infrastructure
    strategy:
      matrix:
        image:
          - name: spark-base
            dockerfile: docker/spark/spark-base.Dockerfile
          - name: kafka-consumer
            dockerfile: docker/kafka/Dockerfile
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
      
      - name: Configure Docker for GCR
        run: |
          gcloud auth configure-docker ${{ env.GCR_HOSTNAME }}
      
      - name: Build Docker image
        run: |
          docker build \
            -t ${{ env.GCR_HOSTNAME }}/${{ env.PROJECT_ID }}/${{ matrix.image.name }}:${{ github.sha }} \
            -t ${{ env.GCR_HOSTNAME }}/${{ env.PROJECT_ID }}/${{ matrix.image.name }}:latest \
            -f ${{ matrix.image.dockerfile }} .
      
      - name: Push to GCR
        run: |
          docker push ${{ env.GCR_HOSTNAME }}/${{ env.PROJECT_ID }}/${{ matrix.image.name }}:${{ github.sha }}
          docker push ${{ env.GCR_HOSTNAME }}/${{ env.PROJECT_ID }}/${{ matrix.image.name }}:latest

  deploy-dbt-models:
    runs-on: ubuntu-latest
    needs: deploy-infrastructure
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dbt
        run: pip install dbt-bigquery
      
      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      
      - name: dbt Deps
        working-directory: dbt
        run: dbt deps
      
      - name: dbt Seed
        working-directory: dbt
        run: dbt seed --target ${{ github.event.inputs.environment }}
      
      - name: dbt Run (Staging)
        working-directory: dbt
        run: dbt run --select staging --target ${{ github.event.inputs.environment }}
      
      - name: dbt Test
        working-directory: dbt
        run: dbt test --target ${{ github.event.inputs.environment }}
      
      - name: dbt Run (Marts)
        working-directory: dbt
        if: success()
        working-directory: dbt
        run: dbt run --select marts --target ${{ github.event.inputs.environment }}
      
      - name: dbt Docs Generate
        working-directory: dbt
        run: dbt docs generate --target ${{ github.event.inputs.environment }}
      
      - name: Upload dbt Docs
        uses: actions/upload-artifact@v3
        with:
          name: dbt-docs
          path: dbt/target/

  integration-tests:
    runs-on: ubuntu-latest
    needs: [build-docker-images, deploy-dbt-models]
    steps:
      - uses: actions/checkout@v3
      
      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      
      - name: Run integration tests
        run: |
          python -m pytest tests/integration/ \
            --environment=${{ github.event.inputs.environment }} \
            --project-id=${{ env.PROJECT_ID }}

  notify-completion:
    runs-on: ubuntu-latest
    needs: [integration-tests]
    if: always()
    steps:
      - name: Send Slack notification
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'Deployment to ${{ github.event.inputs.environment }} ${{ job.status }}'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
        if: always()
```

---

## 4. 本地开发工作流

### 开发环境设置
```bash
# 1. 创建开发分支
git checkout -b feature/your-feature

# 2. 安装所有依赖
pip install -r streaming_pipeline/kafka/requirements.txt
pip install -r batch_pipeline/data_modeling/requirements.txt
pip install dbt-bigquery

# 3. 运行本地检查
black .
pylint streaming_pipeline/ batch_pipeline/
mypy streaming_pipeline/

# 4. 运行单元测试
pytest tests/ --cov

# 5. 运行 dbt 验证
cd dbt
dbt deps
dbt parse
dbt compile
dbt test

# 6. 推送代码
git push origin feature/your-feature
```

### Pre-commit Hook 配置
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/PyCQA/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/PyCQA/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        additional_dependencies: [flake8-docstrings]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-merge-conflict

  - repo: https://github.com/terraform-docs/terraform-docs
    rev: v0.17.0
    hooks:
      - id: terraform-docs
```

---

## 5. 环境配置管理

### 环境变量模板
```bash
# .env.example
# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC=supply_chain_orders

# GCP
GCP_PROJECT_ID=stellar-stream-485314-p0
GCS_BUCKET=supply-chain-data-bucket-485314
BIGQUERY_DATASET=supply_chain_bigquery

# dbt
DBT_PROFILES_DIR=dbt
DBT_TARGET=dev

# Logging
LOG_LEVEL=INFO
```

### 环境特定配置
```yaml
# dbt/profiles.yml
supply_chain_project:
  outputs:
    dev:
      type: bigquery
      project: stellar-stream-485314-p0
      dataset: supply_chain_dbt_dev
      threads: 4
      timeout_seconds: 300
      location: us-central1
      priority: interactive
    
    staging:
      type: bigquery
      project: stellar-stream-485314-p0
      dataset: supply_chain_dbt_staging
      threads: 8
      timeout_seconds: 600
      location: us-central1
      priority: interactive
    
    prod:
      type: bigquery
      project: stellar-stream-485314-p0
      dataset: supply_chain_bigquery
      threads: 16
      timeout_seconds: 900
      location: us-central1
      priority: batch
  
  target: dev
```

---

## 6. 监控和告警

### 关键指标
```
Pipeline Health Checks:
├── Streaming latency: < 5 minutes
├── Batch success rate: > 99.9%
├── dbt test pass rate: 100%
├── Data freshness: < 24 hours
├── BigQuery costs: Tracked daily
└── Error rate: < 0.1%
```

### Monitoring 配置示例
```python
# monitoring/pipeline_monitor.py
from google.cloud import monitoring_v3

def create_alert_policy():
    """创建 BigQuery 数据新鲜度告警"""
    client = monitoring_v3.AlertPolicyServiceClient()
    
    policy = {
        "display_name": "Order Data Freshness Alert",
        "conditions": [
            {
                "display_name": "Data not refreshed in 24 hours",
                "condition_threshold": {
                    "filter": """
                        resource.type="bigquery_resource"
                        AND metric.type="bigquery.googleapis.com/job/num_in_flight_jobs"
                    """,
                    "comparison": monitoring_v3.ComparisonType.COMPARISON_LT,
                    "threshold_value": 1,
                    "duration": "3600s"
                }
            }
        ],
        "notification_channels": [SLACK_CHANNEL_ID],
    }
    
    return client.create_alert_policy(name=parent, alert_policy=policy)
```

---

## 7. 部署清单

### Pre-Deployment Checklist
- [ ] 所有单元测试通过
- [ ] dbt 测试 100% 通过
- [ ] Code coverage > 80%
- [ ] 无安全漏洞（bandit, tfsec）
- [ ] Terraform plan 审核通过
- [ ] 性能基准测试完成
- [ ] 文档更新完成
- [ ] 变更日志更新

### Post-Deployment Validation
- [ ] BigQuery 表数据完整
- [ ] dbt 文档生成成功
- [ ] 监控告警配置正确
- [ ] 日志聚合工作正常
- [ ] 性能指标达到预期
- [ ] 相关团队通知

---

## 8. 回滚策略

### dbt 回滚
```bash
# 查看历史 dbt 运行
dbt run-results.json

# 恢复到之前的模型版本
git checkout main~1 -- dbt/models/
dbt run
```

### BigQuery 回滚
```bash
# 创建表快照（生产环境推荐）
bq cp \
  stellar-stream-485314-p0:supply_chain_bigquery.fact_order \
  stellar-stream-485314-p0:supply_chain_bigquery.fact_order_backup_$(date +%s)

# 从快照恢复
bq cp \
  stellar-stream-485314-p0:supply_chain_bigquery.fact_order_backup_TIMESTAMP \
  stellar-stream-485314-p0:supply_chain_bigquery.fact_order
```

### Terraform 回滚
```bash
terraform destroy -var-file="prod.tfvars"  # 销毁资源
git revert <commit-hash>
terraform apply
```

---

## 9. 成本优化

### GCP 成本管理
```bash
# 监控 BigQuery 查询成本
bq ls --project_id=stellar-stream-485314-p0 --max_results=100 \
  -a --format=prettyjson | jq '.[] | .totalBytes'

# 设置 BigQuery slot reservation
gcloud bigquery reservations create \
  --location=us-central1 \
  --project=stellar-stream-485314-p0 \
  slot-reservation-prod

# 使用分区表减少扫描数据
ALTER TABLE supply_chain_bigquery.fact_order
PARTITION BY order_date;
```

---

## 10. 下一步行动

### 立即实施 (Week 1-2)
- [ ] 创建 GitHub Actions workflow 文件
- [ ] 配置 GCP 服务账户和密钥
- [ ] 设置代码检查工具
- [ ] 创建测试框架

### 短期计划 (Week 3-4)
- [ ] 部署 dbt 测试覆盖率
- [ ] 设置监控和告警
- [ ] 创建部署管道
- [ ] 文档完善

### 长期计划 (Month 2-3)
- [ ] 性能基准测试框架
- [ ] 成本优化分析
- [ ] 容灾恢复计划
- [ ] 自动化回滚机制
