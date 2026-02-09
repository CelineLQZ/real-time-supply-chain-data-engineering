# dbt Source 定义和数据去重指南

## 1. dbt Source 识别原理

### 什么是 Source？
Source 是 dbt 中对外部数据源（通常是原始数据）的定义和引用。在 dbt 中，source 可以是：
- BigQuery 中的原始数据表
- 从数据湖或数据仓库导入的原始数据
- 任何需要通过 `source()` 函数引用的外部数据

### dbt 如何识别 Source？
dbt 通过 `schema.yaml` 或 `schema.yml` 文件来定义和识别 source：

```yaml
version: 2

sources:
  - name: staging                          # source 名称
    database: stellar-stream-485314-p0     # GCP 项目 ID
    schema: supply_chain_bigquery          # BigQuery 数据集名称
    tables:
      - name: dim_customer                 # 表名称
        columns:
          - name: customer_id              # 列定义
            description: ...
```

### 在 Model 中引用 Source
在 SQL 模型中，使用 `source()` 函数来引用：

```sql
from {{ source('staging', 'dim_customer') }}
--         ^              ^
--      source名称      表名称
```

### 识别过程
1. dbt 解析 `schema.yaml` 文件
2. 从中读取 `sources` 部分的定义
3. 当执行 `dbt run` 时，使用 source 定义中的 database.schema.table_name 来访问实际表
4. dbt 可以追踪 source 和 model 之间的数据血缘关系

---

## 2. 当前项目的 Source 配置

### 配置位置
- **文件路径**：`dbt/models/staging/schema.yaml`
- **Source 名称**：`staging`
- **数据库**：`stellar-stream-485314-p0` （GCP 项目）
- **Schema（数据集）**：`supply_chain_bigquery` （BigQuery 数据集）

### 定义的 Source 表
当前定义了 7 个 source 表：

| Source 表名 | 对应的 Staging Model | 主要用途 |
|-----------|------------------|--------|
| `dim_customer` | `stg_dim_customer` | 客户维度数据 |
| `dim_department` | `stg_dim_department` | 部门维度数据 |
| `dim_location` | `stg_dim_location` | 位置维度数据 |
| `dim_product` | `stg_dim_product` | 产品维度数据 |
| `dim_order` | `stg_dim_order` | 订单事实数据 |
| `dim_shipping` | `stg_dim_shipping` | 运输维度数据 |
| `dim_metadata` | `stg_dim_metadata` | 元数据 |

---

## 3. 数据去重策略

### 去重的原因
在流式数据处理管道中，由于重试机制、分布式系统的特性等，同一条数据可能被重复处理，导致目标表中存在重复记录。

### 去重方法：ROW_NUMBER() Over PARTITION BY

每个 staging model 都实现了以下模式：

```sql
with source_data as (
    select
        column1,
        column2,
        ...
        -- 按主键分区，对每组重复记录进行编号
        row_number() over (
            partition by primary_key 
            order by primary_key
        ) as rn
    from {{ source('staging', 'source_table') }}
)
-- 只保留 rn = 1 的记录（即每个主键的第一条记录）
select * except(rn) 
from source_data 
where rn = 1
```

### 各表的去重分区键

| Model | 分区键（Primary Key） | 说明 |
|------|------------------|------|
| `dim_customer` | `Customer_Id` | 客户 ID |
| `dim_department` | `Department_Id` | 部门 ID |
| `dim_location` | `Order_Zipcode` | 订单邮编 |
| `dim_order` | `Order_Id` | 订单 ID |
| `dim_product` | `Product_Card_Id` | 产品卡 ID |
| `dim_shipping` | `Shipping_date`, `Shipping_Mode` | 运输日期和模式的组合 |
| `dim_metadata` | `key` | 元数据键 |

### 去重的优势
1. **消除重复数据**：确保每个主键只有一条记录
2. **数据质量**：避免重复数据导致的聚合错误
3. **成本优化**：减少存储和计算开销
4. **可审计性**：通过 `rn` 列可以追踪哪些数据是重复的

---

## 4. 验证 Source 配置

### 检查 Source 是否被正确识别

运行以下命令：

```bash
# 在 dbt 目录中
export DBT_PROFILES_DIR=~/.dbt
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/gcp-cred.json

# 解析项目（检查 source 定义）
dbt parse

# 查看 source 的血缘关系
dbt docs generate
dbt docs serve  # 然后在浏览器中查看 http://localhost:8000
```

### 常见的 Source 识别问题

#### 问题 1：Source 定义错误
**错误消息**：`Could not find source 'staging.dim_customer'`

**原因**：
- schema.yaml 中 source 名称拼写错误
- database 或 schema 名称不正确
- YAML 缩进错误

**解决方案**：
```yaml
sources:
  - name: staging                    # 确保这个名称与 model 中 source() 函数的第一个参数匹配
    database: stellar-stream-485314-p0
    schema: supply_chain_bigquery
```

#### 问题 2：Source 表找不到
**错误消息**：`Not found: Dataset stellar-stream-485314-p0:supply_chain_bigquery`

**原因**：
- BigQuery 数据集名称错误
- 凭证没有访问该数据集的权限
- 数据集不存在

**解决方案**：
```bash
# 验证数据集是否存在
bq ls --project_id=stellar-stream-485314-p0

# 列出数据集中的表
bq ls --project_id=stellar-stream-485314-p0 supply_chain_bigquery
```

#### 问题 3：数据库项目 ID 错误
**症状**：连接失败，提示项目不存在

**检查步骤**：
```bash
# 检查当前 GCP 项目
gcloud config get-value project

# 设置正确的项目
gcloud config set project stellar-stream-485314-p0
```

---

## 5. 工作流程总结

```
原始数据 (supply_chain_bigquery)
    ↓
Staging Models (使用 source() 引用)
    ↓
ROW_NUMBER() 去重
    ↓
去重后的 Staging Views
    ↓
Marts Models (创建业务模型)
    ↓
最终分析表
```

---

## 6. 运行 dbt Pipeline

### 基本命令

```bash
# 1. 进入 dbt 目录
cd dbt/

# 2. 测试连接
export DBT_PROFILES_DIR=.
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/gcp-cred.json
dbt debug

# 3. 解析项目（验证 source 和 model）
dbt parse

# 4. 运行所有 model
dbt run

# 5. 只运行 staging model
dbt run --select staging

# 6. 只运行特定 model
dbt run --select stg_dim_customer

# 7. 运行测试
dbt test

# 8. 生成文档
dbt docs generate
dbt docs serve
```

### 验证去重效果

```sql
-- 在 BigQuery 中查询去重前的数据
select count(*) as total_records
from `stellar-stream-485314-p0.supply_chain_bigquery.dim_customer`;

-- 查询去重后的数据
select count(*) as deduplicated_records
from `stellar-stream-485314-p0.supply_chain_dbt_dev.stg_dim_customer`;

-- 比较差异
-- 如果 deduplicated_records < total_records，说明去重成功
```

---

## 7. 常见问题解答

### Q: dbt 怎样才能识别我定义的 source？
**A**: dbt 会自动读取项目目录中所有名为 `schema.yml` 或 `schema.yaml` 的文件，从中解析 sources 定义。确保：
- 文件名正确
- YAML 格式正确
- source 名称与 SQL 中 `source()` 函数的参数一致

### Q: 为什么 dbt run 找不到 source 表？
**A**: 最可能的原因是：
1. BigQuery 数据集名称错误（应该是 `supply_chain_bigquery`）
2. GCP 项目 ID 错误（应该是 `stellar-stream-485314-p0`）
3. 凭证文件权限不足或路径错误
4. BigQuery 数据集不存在

### Q: 去重后会丢失数据吗？
**A**: 不会。ROW_NUMBER() 方法只是选择每个主键组中的第一条记录，其他记录被排除。这正是我们想要的效果。如果需要保留所有数据来分析重复原因，可以：
- 在一个临时表中保存原始数据
- 使用 `row_number()` 生成一个 `duplicate_flag` 列来标记重复数据

### Q: 如何追踪数据血缘关系？
**A**: 运行 `dbt docs generate` 后，在文档中查看数据血缘图：
```bash
dbt docs generate
dbt docs serve  # 访问 http://localhost:8000
```
在网页中可以看到从 source 到 staging model 到 marts model 的完整数据流。

---

## 8. 最佳实践

### ✅ 应该做的
- ✅ 为每个 source 提供清晰的描述
- ✅ 为关键列添加测试（unique, not_null）
- ✅ 定期验证 source 数据的完整性
- ✅ 使用 dbt test 来自动验证去重效果
- ✅ 在 Git 中追踪 schema.yaml 的变化

### ❌ 不应该做的
- ❌ 不要在 model 中直接硬编码表名（应使用 source()）
- ❌ 不要忽视去重逻辑，假设源数据没有重复
- ❌ 不要使用错误的数据库/schema 名称
- ❌ 不要在生产环境中使用不经过测试的 source 配置

---

## 9. 参考资源

- [dbt Source 官方文档](https://docs.getdbt.com/docs/build/sources)
- [dbt ref() vs source() 的区别](https://docs.getdbt.com/docs/build/ref)
- [BigQuery 数据导入到 dbt](https://docs.getdbt.com/docs/build/using-sources)
