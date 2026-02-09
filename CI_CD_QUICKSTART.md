# CI/CD 快速开始指南

## 1️⃣ 本地开发环境设置

### 安装 pre-commit hooks
```bash
cd /Users/liceline/Documents/study_material/data_engineer/project_study/supply_chain/supply_chain_de_study

# 安装 pre-commit
pip install pre-commit

# 安装 hooks
pre-commit install

# 测试 hooks（可选）
pre-commit run --all-files
```

### 创建开发分支
```bash
git checkout -b feature/your-feature-name
```

---

## 2️⃣ 本地代码检查

### 运行所有检查
```bash
# 代码格式化
black .

# 导入排序
isort streaming_pipeline/ batch_pipeline/

# Linting
flake8 streaming_pipeline/ batch_pipeline/

# 类型检查
mypy streaming_pipeline/kafka/ batch_pipeline/

# 安全扫描
bandit -r streaming_pipeline/ batch_pipeline/

# dbt 验证
cd dbt
dbt parse
dbt compile
cd ..

# 运行测试
pytest tests/ -v --cov
```

### 快捷命令
创建 `Makefile`:
```makefile
.PHONY: lint test format check-all

lint:
	pylint streaming_pipeline/ batch_pipeline/

format:
	black .
	isort streaming_pipeline/ batch_pipeline/

check-all: format lint
	mypy streaming_pipeline/
	pytest tests/ -v --cov

dbt-check:
	cd dbt && dbt parse && dbt compile && cd ..
```

运行检查：
```bash
make check-all
make dbt-check
```

---

## 3️⃣ 推送代码到 GitHub

### 提交代码
```bash
# 查看变更
git status

# 添加文件
git add .

# 提交（自动运行 pre-commit hooks）
git commit -m "feat: describe your changes"

# 推送
git push origin feature/your-feature-name
```

### 创建 Pull Request
1. 访问 GitHub 仓库
2. 点击 "New Pull Request"
3. 选择 `feature/your-feature-name` → `develop`
4. 填写 PR 描述
5. 等待自动 CI 检查通过

---

## 4️⃣ 部署到不同环境

### 部署到 Dev 环境
```bash
# 直接推送到 develop 分支
git checkout develop
git merge feature/your-feature-name
git push origin develop

# 或在 GitHub UI 上 merge PR
# CI 流程会自动运行
```

### 部署到 Staging/Prod 环境
1. 在 GitHub 仓库 → "Actions" 标签页
2. 选择 "Deploy Pipeline" 工作流
3. 点击 "Run workflow"
4. 选择环境（staging 或 prod）
5. 检查 approval 复选框
6. 点击 "Run workflow"

---

## 5️⃣ 监控部署进度

### 查看 CI/CD 状态
```bash
# 本地查看最近提交的检查状态
git log --oneline -n 5

# 在 GitHub 上查看：
# - Actions → Workflows → CI Pipeline / Deploy Pipeline
# - 点击最新的运行查看详细日志
```

### 常见问题排查

#### dbt 测试失败
```bash
cd dbt
dbt test --target dev  # 本地测试
dbt test --select failed_model  # 只测试失败的模型
```

#### Python 代码风格问题
```bash
# 自动修复格式问题
black streaming_pipeline/ batch_pipeline/
isort streaming_pipeline/ batch_pipeline/
```

#### Terraform 计划失败
```bash
cd terraform/
terraform init
terraform plan -var-file="dev.tfvars"  # 查看具体错误
```

---

## 6️⃣ 部署检查清单

### 提交前检查
- [ ] 运行 `make check-all` 通过
- [ ] dbt 测试通过：`cd dbt && dbt test`
- [ ] Terraform 验证通过：`terraform validate`
- [ ] 更新了相关文档
- [ ] 编写了测试用例

### 部署前检查
- [ ] PR 获得了至少 1 个 approval
- [ ] GitHub Actions CI 全部通过 ✅
- [ ] dbt 文档已生成
- [ ] BigQuery 数据质量检查通过
- [ ] 监控告警已配置

---

## 7️⃣ 紧急回滚

### 回滚 dbt 模型
```bash
# 查看上一个成功的版本
git log --oneline dbt/

# 恢复到上一个版本
git checkout HEAD~1 -- dbt/models/

# 推送恢复
git commit -m "revert: rollback dbt models due to data quality issue"
git push origin main
```

### 回滚 BigQuery 数据
```bash
# 查看备份表
bq ls --project_id=stellar-stream-485314-p0 | grep backup

# 从备份恢复
bq cp \
  stellar-stream-485314-p0:supply_chain_bigquery.fact_order_backup_TIMESTAMP \
  stellar-stream-485314-p0:supply_chain_bigquery.fact_order
```

---

## 8️⃣ 环境变量配置

### 设置 GitHub Secrets

在 GitHub 仓库设置中添加以下 secrets：

| Secret 名称 | 描述 | 来源 |
|-----------|------|-----|
| `GCP_SA_KEY` | GCP 服务账户密钥 (JSON) | GCP Console |
| `SLACK_WEBHOOK` | Slack 通知 webhook | Slack App |

### 本地 .env 文件
```bash
# .env
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC=supply_chain_orders

GCP_PROJECT_ID=stellar-stream-485314-p0
GCS_BUCKET=supply-chain-data-bucket-485314
BIGQUERY_DATASET=supply_chain_bigquery

DBT_PROFILES_DIR=dbt
DBT_TARGET=dev

LOG_LEVEL=INFO
```

---

## 9️⃣ 性能优化建议

### 加速 CI 流程
```yaml
# 并行运行检查（GitHub Actions 已配置）
jobs:
  code-quality:   # 耗时: ~2-3 分钟
  dbt-validation: # 耗时: ~3-5 分钟
  unit-tests:     # 耗时: ~1-2 分钟
  # 以上并行运行，总耗时: ~5 分钟
```

### dbt 性能优化
```bash
# 增加线程数加速执行
dbt run --threads 8

# 只运行修改过的模型
dbt run --select state:modified+
```

---

## 🔟 文档和资源

### 关键文档
- [CI/CD 完整策略](CI_CD_STRATEGY.md)
- [dbt 文档](dbt/dbt_pipeline.md)
- [Terraform 文档](terraform/terraform_note.md)
- [Streaming Pipeline 指南](streaming_pipeline/kafka/README.md)
- [Batch Pipeline 指南](batch_pipeline/data_modeling/BATCH_PIPELINE_EXECUTION_GUIDE.md)

### 外部资源
- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [dbt 最佳实践](https://docs.getdbt.com/guides/best-practices)
- [Terraform 文档](https://www.terraform.io/docs)
- [BigQuery 最佳实践](https://cloud.google.com/bigquery/docs/best-practices)

---

## 💡 常用命令速查表

```bash
# Git 相关
git checkout -b feature/name    # 创建分支
git add .                       # 暂存文件
git commit -m "message"         # 提交
git push origin branch          # 推送
git pull origin main            # 拉取

# dbt 相关
dbt deps                        # 安装依赖
dbt parse                       # 解析模型
dbt compile                     # 编译模型
dbt run                         # 执行模型
dbt test                        # 运行测试
dbt docs generate               # 生成文档

# Terraform 相关
terraform init                  # 初始化
terraform plan                  # 计划
terraform apply                 # 应用
terraform destroy               # 销毁

# Python 相关
pytest tests/                   # 运行测试
black .                         # 代码格式化
flake8 .                        # 代码检查
mypy streaming_pipeline/        # 类型检查
bandit -r .                     # 安全检查
```

---

## 📞 获取帮助

- 遇到问题？检查 GitHub Issues
- 想提建议？提交 Pull Request
- 需要帮助？联系数据工程团队
