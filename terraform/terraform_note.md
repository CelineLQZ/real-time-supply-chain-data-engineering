
# Terraform + GCP 
在使用 Terraform 管理 GCP 资源时，我先在 GCP Console 中完成 Project 和 Service Account 的创建与权限配置，然后在本地通过 Terraform Provider 与 GCP 建立认证关系。完成 provider 配置后，我使用 Terraform 分别创建了 GCS Bucket 作为 Data Lake，以及 BigQuery Dataset 作为 Data Warehouse，并通过 variables.tf 对配置进行了模块化和规范化。在terraform路径下，只有main.tf和variables.tf是我编辑的，其他文件是terraform在运行时出现的系统文件。

## 使用 Terraform 配置 Google Cloud Platform（GCP）服务：前置准备流程整理

在使用 Terraform 管理和配置 Google Cloud Platform（GCP）资源之前，需要先在 GCP Console 中完成一系列基础配置。这些步骤是 Terraform 能够正常与 GCP 交互的前提。

---

### 1. 在 GCP Console 中创建 Project

* 首先，在 **Google Cloud Platform Console** 中新建一个 Project
* 创建完成后，需要进入 **Dashboard**，确认并记录该 Project 的 **Project ID**

  * ⚠️ 注意：**Terraform 使用的是 Project ID，而不是 Project Name**
  * Project Name 只是展示用，不能用于 API 或 Terraform 配置

---

### 2. 在 Project 下创建 Service Account

* 在该 Project 下新建一个 **Service Account**
* 该 Service Account 用于 Terraform 与 GCP 之间的身份认证和权限控制

#### 为 Service Account 分配必要的权限（IAM Roles）

根据 Terraform 要管理的资源，为 Service Account 分配相应权限，例如：

* Google Cloud Storage 相关权限（如 Storage Admin / Storage Object Admin）
* BigQuery 相关权限（如 BigQuery Admin / BigQuery Data Editor）

这些权限确保 Terraform 可以创建、修改和管理对应的 GCP 资源。

---

### 3. 为 Service Account 创建 Key（JSON）

* 在 Service Account 中 **Create a new key**
* 选择 **JSON** 格式
* 下载生成的 `application API JSON key`

---

### 4. 在本地保存 GCP Credentials

* 将下载的 JSON key 文件：

  * 要么直接保存在本地（例如 `~/keys/mycredentials.json`）
  * 要么将其内容复制并保存到本地统一管理的 credentials 文件中
* 后续 Terraform 会通过该 JSON key 与 GCP API 进行身份认证

---

### 5. ⚠️ 重要注意：新版本 GCP 对 Application JSON Key 的限制

在 **新版 Google Cloud Platform** 中：

* **默认不再允许**直接通过 Service Account 的 Application JSON Key
* 从本地环境与 GCP 进行交互
* 这是出于安全考虑（Organization Policy 限制）

---

### 6. 处理方式：从 Project 级别回到 Organization / 全局层级

当遇到上述限制时，需要：

* 从当前的 **specific project** 跳出
* 回到 **整个 GCP Console 的 Organization / 全局管理层级**
* 在该层级中，会有一个用于管理所有 Projects 的 **组织级账号**

  * 通常带有“建筑 / Organization”标识
* 在这里：

  * 需要配置或修改 **Organization Policy**
  * 显式允许使用 **Service Account JSON Key** 进行本地 API 访问
  * 从而使 Terraform 可以通过 `application_credentials.json` 正常与 GCP 交互

太好了，这一段已经**完全是“会做的人在复盘流程”**了 👍
我继续**在你刚才那一版的基础上往下整理**，保持同一种「实习笔记 / 方法论说明」的风格，把 **Terraform 部分**理顺、写清楚、可复用。

---

## 使用 Terraform 配置 GCP 服务（Terraform 实操流程）

在完成 GCP 侧的 Project、Service Account、权限与 Credentials 准备之后，就可以正式开始使用 Terraform 对 GCP 资源进行管理。

---

### 8. 在本地项目中创建 Terraform 工作目录

* 在当前项目（project）的根目录下，新建一个专门用于 Terraform 的文件夹，例如：

```
/terraform
```

* 进入该目录后，新建 Terraform 主配置文件：

```
main.tf
```

> 说明：
> `main.tf` 是 Terraform 的核心配置文件，用于定义 provider 以及所有要创建的云资源。

---

### 9. 配置 GCP Terraform Provider（main.tf 顶部）

#### 查找官方 Terraform GCP 文档

* 在浏览器中搜索：
  **Terraform GCP**
* 进入 **Terraform 官方文档**
* 找到 Google Cloud Platform Provider 页面
* 在页面右上方可以看到一个 **Usage / Example**

#### 复制 Provider 示例代码

* 将 Usage 示例中的代码：

  * **完整复制**
  * 粘贴到 `main.tf` 的最顶端

通常这部分代码包含两段：

1. `terraform {}`（版本与 provider 声明）
2. `provider "google" {}`（GCP provider 配置）

---

### 10. 填写 GCP Provider 的 Configuration

在 `provider "google"` 配置中，需要填写以下关键信息（均可在官方文档中找到说明）：

* `project`

  * 填写 **GCP Project ID**
* `region` / `location`（如有需要）
* **credentials（可选但实际非常重要）**

#### 指定本地 JSON Key（credentials）

可以在 provider 中新增一行：

```hcl
credentials = file("path/to/mycredentials.json")
```

* 指向本地保存的 Service Account JSON key
* 这样 Terraform 在本地执行时，就会使用该 Service Account 与 GCP 进行交互

完成以上配置后：

✅ 本地 Terraform
↔️
✅ GCP Project 中的 Service Account
已经可以成功联通

---

### 11. 使用 Terraform 创建 GCS Bucket（作为 Data Lake）

#### 查找 GCS Terraform 官方文档

* 搜索：
  **Terraform Google Cloud Storage bucket**
* 打开 Terraform 官方文档
* 找到 `google_storage_bucket` 的示例代码

#### 将 Bucket 配置复制到 main.tf

在 `main.tf` 中粘贴 bucket 相关代码，并根据需要修改以下关键参数：

* **Bucket 名称**

  * 自定义为符合项目命名规范的名称
* **生命周期规则（Lifecycle Rule）**

  * 设置自动删除策略
  * 例如：**30 天后自动删除 bucket 中的对象**

这一步的目的：

* 创建一个 GCS Bucket
* 用作项目的 **Data Lake**

---

### 12. 测试 Terraform 是否正常工作

进入 Terraform 目录，在终端中依次执行：

```bash
terraform init
```

* 初始化 Terraform
* 下载所需 provider
* 如果该步骤成功，说明配置正确

接着执行：

```bash
terraform plan
terraform apply
```

* `plan`：查看即将创建的资源
* `apply`：真正创建资源

> 过程中会生成很多 `.terraform`、`.lock` 等文件
> 👉 **这些都不用手动修改，也不需要特别关注**
> 你自己维护的核心文件只有：
> **`main.tf`**

---

### 13. 验证结果（GCP Console）

* 回到 Google Cloud Platform Console
* 进入 Cloud Storage
* 可以看到 Terraform 创建的 GCS Bucket
* 至此，**Terraform ↔️ GCP 的完整链路验证成功**

---

### 14. 使用 Terraform 创建 BigQuery Dataset（作为 Data Warehouse）

#### 查找 BigQuery Terraform 官方文档

* 搜索：
  **Terraform BigQuery dataset**
* 进入 Terraform 官方文档
* 找到 BigQuery Dataset 的配置示例

#### 添加 BigQuery 配置到 main.tf

* 将 BigQuery Dataset 的示例代码复制到 `main.tf`
* 按与 GCS 类似的方式：

  * 修改 Dataset 名称
  * 设置 Project ID
  * 设置 Location 等参数

执行：

```bash
terraform plan
terraform apply
```

完成后：

* 在 GCP Console → BigQuery 中
* 可以看到新创建的 Dataset
* 该 Dataset 即作为 **Data Warehouse**

---

### 15. 使用 variables.tf 重构配置（进阶）

在所有资源都可以正常创建之后：

* 将 `main.tf` 中的硬编码值（如 project_id、bucket_name 等）
* 抽离为变量

做法：

1. 让 AI Agent 根据当前 `main.tf` 自动生成 `variables.tf`
2. 修改 `main.tf`，使用 `var.xxx` 引用变量
3. 提升配置的：

   * 可读性
   * 可复用性
   * 专业度（非常符合实习 / 项目标准）

┌──────────────────────────┐
│        本地开发环境        │
│                          │
│  Terraform CLI           │
│  main.tf / variables.tf  │
│                          │
└───────────┬──────────────┘
            │
            │ credentials (JSON key)
            ▼
┌──────────────────────────┐
│      GCP Service Account │
│      (IAM Roles)         │
│                          │
│  - Storage permissions   │
│  - BigQuery permissions  │
└───────────┬──────────────┘
            │
            │ API calls
            ▼
┌──────────────────────────┐
│        GCP Project       │
│                          │
│  ┌───────────────────┐  │
│  │ GCS Bucket         │◄─┤  Data Lake
│  │ (Terraform)        │  │
│  └───────────────────┘  │
│                          │
│  ┌───────────────────┐  │
│  │ BigQuery Dataset   │◄─┤  Data Warehouse
│  │ (Terraform)        │  │
│  └───────────────────┘  │
└──────────────────────────┘







