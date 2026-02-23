# Real-Time Supply Chain Data Engineering Platform

<div align="center">

![GitHub](https://img.shields.io/badge/GitHub-Actions-2088FF?logo=github)
![dbt](https://img.shields.io/badge/dbt-1.8.2-FF6849)
![BigQuery](https://img.shields.io/badge/Google-BigQuery-3DDC84?logo=google-cloud)
![Kafka](https://img.shields.io/badge/Apache-Kafka-7.4.0-231F20?logo=apache-kafka)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)

**A comprehensive data engineering platform combining real-time streaming and batch processing for supply chain analytics**

[Features](#features) • [Architecture](#architecture) • [Quick Start](#quick-start) • [Documentation](#documentation) • [Contributing](#contributing)

</div>

---

## 📋 Overview

This project implements a **production-grade data engineering platform** for supply chain analytics, combining:
- 🔴 **Real-time streaming** via Kafka
- ⚙️ **Batch processing** via Spark
- 📊 **Data modeling** via dbt
- ☁️ **Cloud infrastructure** via Google Cloud Platform (GCS + BigQuery)
- 🔄 **CI/CD automation** via GitHub Actions

The platform processes supply chain data (orders, inventory, shipping, customers) and produces analytical tables for business intelligence and decision-making.

---

## 🎯 Features

### ✨ Core Capabilities

| Feature | Description |
|---------|-----------|
| **Real-time Streaming** | Kafka producer/consumer pipeline with configurable buffer sizes and fetch limits |
| **Batch ETL Pipeline** | Spark-based data transformation with automatic column standardization |
| **Data Warehouse** | BigQuery with dbt-managed dimensional modeling (staging + marts) |
| **Infrastructure as Code** | Terraform for GCS buckets, BigQuery datasets, and service accounts |
| **Automated Testing** | Python unit tests, dbt model tests, and integration tests |
| **CI/CD Workflows** | GitHub Actions for code quality, validation, and multi-environment deployment |
| **Docker Containerization** | Pre-configured images for Kafka, Spark, and Airflow |
| **Data Quality** | Duplicate detection, null value analysis, and data profiling |

---

## 🏗️ Architecture

```
┌──────────────────┐
│   Raw Data       │
│  (CSV Files)     │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────────────┐
│  INGESTION LAYER                     │
│  ├─ Kafka Producer (Streaming)       │
│  └─ Schema Registry & Control Center │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│  STORAGE LAYER (Bronze)              │
│  ├─ GCS: raw_streaming/              │
│  ├─ PostgreSQL (Local)               │
│  └─ Kafka Topic: supply_chain_data   │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│  TRANSFORMATION LAYER                │
│  ├─ Spark Batch Pipeline             │
│  │  ├─ Data Cleaning                 │
│  │  ├─ Column Standardization        │
│  │  ├─ Duplicate Removal             │
│  │  └─ Star Schema Generation        │
│  └─ Processing Engine: PySpark 4.1.1 │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│  STORAGE LAYER (Silver)              │
│  ├─ GCS: transformed_data/           │
│  └─ Format: Parquet (Columnar)       │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│  LOADING LAYER                       │
│  ├─ BigQuery Loader                  │
│  ├─ Project: stellar-stream-485314   │
│  └─ Dataset: supply_chain_bigquery   │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│  MODELING LAYER (dbt)                │
│  ├─ Staging Models (6 views)         │
│  │  ├─ dim_order.sql                 │
│  │  ├─ dim_customer.sql              │
│  │  ├─ dim_location.sql              │
│  │  ├─ dim_product.sql               │
│  │  ├─ dim_department.sql            │
│  │  └─ dim_shipping.sql              │
│  └─ Mart Models (6 tables)           │
│     ├─ overall_performance.sql       │
│     ├─ inventory_levels.sql          │
│     ├─ customer_retention_rate.sql   │
│     ├─ financial_commitments.sql     │
│     ├─ fraud_detection.sql           │
│     └─ payment_delays.sql            │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│  ANALYTICS LAYER                     │
│  ├─ BI Tools (Looker, Tableau, etc) │
│  └─ Data Scientists & Analysts       │
└──────────────────────────────────────┘
```

### Data Flow Summary
1. **Source** → CSV files and real-time events
2. **Ingestion** → Kafka streaming pipeline
3. **Bronze** → Raw data in GCS and Kafka topics
4. **Transformation** → Spark batch processing (clean, standardize, deduplicate)
5. **Silver** → Transformed parquet files in GCS
6. **Loading** → BigQuery tables (facts + dimensions)
7. **Modeling** → dbt staging views + analytical marts
8. **Analytics** → BI dashboards and SQL queries

---

## 🚀 Quick Start

### Prerequisites

- **Python**: 3.10+
- **Java**: OpenJDK 11+ (required for Spark)
- **Docker & Docker Compose**: For containerized services
- **GCP Account**: Project with enabled services (BigQuery, Cloud Storage)
- **Git**: For version control

### Installation

#### 1. Clone the Repository
```bash
git clone https://github.com/CelineLQZ/real-time-supply-chain-data-engineering.git
cd supply_chain_de_study
```

#### 2. Set Up Python Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r batch_pipeline/data_modeling/requirements.txt
pip install -r streaming_pipeline/kafka/requirements.txt
```

#### 3. Configure GCP Credentials
```bash
# Place GCP service account JSON in keys/ directory
cp /path/to/gcp-service-account.json keys/gcp-cred.json

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/keys/gcp-cred.json"
```

#### 4. Set Up Docker Services
```bash
# Start Kafka, Zookeeper, Schema Registry, and Control Center
cd docker/kafka
docker-compose up -d

# Verify services are running
docker-compose ps
```

#### 5. Initialize dbt
```bash
cd dbt
dbt deps  # Install dbt packages
dbt parse  # Validate project structure
```

---

## 📁 Project Structure

```
.
├── README.md                          # Project documentation
├── CI_CD_STRATEGY.md                  # Detailed CI/CD documentation
├── CI_CD_QUICKSTART.md                # Quick CI/CD setup guide
├── pytest.ini                         # pytest configuration
├── .pre-commit-config.yaml            # Pre-commit hooks
│
├── batch_pipeline/                    # Batch ETL Processing
│   ├── run_batch_pipeline.sh          # Main pipeline script
│   └── data_modeling/
│       ├── config.py                  # Batch pipeline config
│       ├── requirements.txt           # Python dependencies
│       ├── transformed_data.py        # Spark transformation logic
│       ├── utilis.py                  # Helper functions & column mappings
│       └── __pycache__/               # Compiled Python files
│
├── streaming_pipeline/                # Real-time Streaming
│   └── kafka/
│       ├── producer.py                # Kafka producer (data source)
│       ├── consumer.py                # Kafka consumer (data sink)
│       ├── kafka_config.py            # Kafka connection settings
│       ├── requirements.txt           # Python dependencies
│       ├── README.md                  # Kafka pipeline guide
│       └── __pycache__/               # Compiled files
│
├── dbt/                               # Data Transformation (DBT)
│   ├── dbt_project.yml                # dbt project config
│   ├── profiles.yml                   # dbt connection profiles
│   ├── dbt_pipeline.md                # dbt pipeline documentation
│   ├── dbt_cloud.yml                  # dbt cloud config
│   ├── SOURCE_AND_DEDUPLICATION_GUIDE.md
│   ├── models/
│   │   ├── staging/                   # Staging models (6 dimensions)
│   │   │   ├── dim_order.sql
│   │   │   ├── dim_customer.sql
│   │   │   ├── dim_location.sql
│   │   │   ├── dim_product.sql
│   │   │   ├── dim_department.sql
│   │   │   └── dim_shipping.sql
│   │   └── marts/                     # Mart models (6 analytics tables)
│   │       ├── overall_performance.sql
│   │       ├── inventory_levels.sql
│   │       ├── customer_retention_rate.sql
│   │       ├── financial_commitments.sql
│   │       ├── fraud_detection.sql
│   │       └── payment_delays.sql
│   ├── tests/                         # dbt tests (schema + data)
│   └── dbt-env/                       # dbt virtual environment
│
├── terraform/                         # Infrastructure as Code
│   ├── main.tf                        # GCP resources (GCS, BigQuery)
│   ├── variables.tf                   # Variable definitions
│   ├── terraform.tfstate              # State file
│   ├── tfplan                         # Execution plan
│   └── terraform_note.md              # Terraform documentation
│
├── docker/                            # Docker Configurations
│   ├── kafka/
│   │   └── docker-compose.yaml        # Kafka stack
│   ├── spark/
│   │   ├── docker-compose.yaml        # Spark cluster
│   │   ├── spark-base.Dockerfile
│   │   ├── spark-master.Dockerfile
│   │   ├── spark-worker.Dockerfile
│   │   ├── cluster-base.Dockerfile
│   │   ├── jupyterlab.Dockerfile
│   │   └── jar_files/                 # Spark dependencies
│   └── airflow/
│       ├── docker-compose.yaml        # Airflow orchestration
│       ├── Dockerfile
│       ├── requirements.txt
│       ├── config/
│       │   └── airflow.cfg
│       ├── dags/                      # Airflow DAGs
│       ├── logs/                      # Airflow execution logs
│       └── plugins/                   # Custom Airflow operators
│
├── data/                              # Sample Data
│   ├── DataCoSupplyChainDataset.csv   # Main supply chain dataset
│   ├── DescriptionDataCoSupplyChain.csv
│   ├── tokenized_access_logs.csv
│   ├── data_exploration.ipynb         # Data profiling notebook
│   ├── data_view.py                   # CLI data exploration tool
│   └── data_dictionary.csv            # Generated metadata
│
├── configs/                           # Global Configuration
│   └── config.py                      # Shared settings
│
├── keys/                              # Credentials (⚠️ .gitignored)
│   └── gcp-cred.json                  # GCP service account (DO NOT COMMIT)
│
├── logs/                              # Execution Logs
│   └── batch_pipeline/                # Batch job logs
│
├── note/                              # Documentation
│   ├── DATA_PIPELINE_FLOW.md          # Data flow visualization
│   ├── BATCH_DATA_PROCESSING.md       # Batch processing guide
│   ├── STREAMING_PIPELINE_GUIDE.md    # Streaming setup guide
│   ├── INGESTION_TRANSFORM_UPLOAD_GUIDE.md
│   ├── PHASE1_INGESTION_DETAILED_GUIDE.md
│   └── TERRAFORM_GUIDE.md             # Infrastructure guide
│
├── tests/                             # Python Unit Tests
│   ├── test_batch_pipeline.py
│   ├── test_kafka_pipeline.py
│   └── test_data_quality.py
│
├── .github/                           # GitHub Configuration
│   └── workflows/
│       ├── ci.yml                     # CI pipeline (linting, tests, validation)
│       └── deploy.yml                 # CD pipeline (dev/staging/prod deployment)
│
└── .gitignore                         # Git ignore rules
```

---

## 🔧 Configuration

### Batch Pipeline Configuration
**File**: `batch_pipeline/data_modeling/config.py`

```python
# Spark Configuration
SPARK_APP_NAME = "supply_chain_etl"
SPARK_MASTER = "local[*]"  # or "spark://master:7077" for cluster

# GCP Configuration
GCP_PROJECT_ID = "stellar-stream-485314"
GCS_BUCKET = "supply-chain-data-bucket-485314"
BIGQUERY_DATASET = "supply_chain_bigquery"

# Data Paths
GCS_RAW_PATH = f"gs://{GCS_BUCKET}/raw_streaming"
GCS_TRANSFORM_PATH = f"gs://{GCS_BUCKET}/transformed_data"
```

### Streaming Pipeline Configuration
**File**: `streaming_pipeline/kafka/kafka_config.py`

```python
KAFKA_BOOTSTRAP_SERVERS = ["localhost:9092"]
KAFKA_TOPIC = "supply_chain_data"
KAFKA_GROUP_ID = "supply_chain_consumer_group"

# Producer Settings
PRODUCER_BATCH_SIZE = 16384
PRODUCER_LINGER_MS = 100

# Consumer Settings
CONSUMER_FETCH_MIN_BYTES = 1024
CONSUMER_FETCH_MAX_WAIT_MS = 500
CONSUMER_BUFFER_SIZE = 20000
CONSUMER_FETCH_MAX_BYTES = 52428800
```

### dbt Configuration
**File**: `dbt/profiles.yml`

```yaml
supply_chain:
  target: dev
  outputs:
    dev:
      type: bigquery
      project: stellar-stream-485314
      dataset: supply_chain_bigquery_dev
      method: service-account
      keyfile: ../keys/gcp-cred.json
      
    staging:
      type: bigquery
      project: stellar-stream-485314
      dataset: supply_chain_bigquery_staging
      
    prod:
      type: bigquery
      project: stellar-stream-485314
      dataset: supply_chain_bigquery_prod
```

---

## 📊 Running the Pipeline

### 1. Streaming Pipeline (Kafka)

#### Start Kafka Services
```bash
cd docker/kafka
docker-compose up -d
```

#### Run Producer (Data Source)
```bash
cd streaming_pipeline/kafka
python producer.py
```

#### Run Consumer (Data Sink)
```bash
cd streaming_pipeline/kafka
python consumer.py
```

### 2. Batch Pipeline (Spark)

#### Execute Full Pipeline
```bash
cd batch_pipeline
bash run_batch_pipeline.sh
```

#### Or Run Components Separately
```bash
# Configure and run batch ETL
cd batch_pipeline/data_modeling
python transformed_data.py

# Load data to BigQuery
python bigquery_loader.py
```

### 3. dbt Modeling

#### Run All Models
```bash
cd dbt
dbt run
```

#### Run Specific Models
```bash
# Staging models only
dbt run --select staging

# Specific mart
dbt run --select overall_performance

# Models + tests
dbt build
```

#### Test Data Quality
```bash
dbt test
```

---

## 🧪 Testing

### Python Unit Tests
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_batch_pipeline.py -v

# Run with coverage
pytest --cov=batch_pipeline --cov=streaming_pipeline tests/
```

### dbt Tests
```bash
cd dbt

# Run schema tests
dbt test

# Run specific test
dbt test --select dim_order
```

### Integration Tests
```bash
# Test end-to-end pipeline
bash scripts/run_integration_tests.sh
```

---

## 🔄 CI/CD Pipeline

This project uses **GitHub Actions** for automated validation and deployment.

### CI Workflow (`.github/workflows/ci.yml`)

Runs on every push and pull request:

1. **Code Quality** (Parallel)
   - Pylint: Python linting
   - Black: Code formatting
   - flake8: Style guide enforcement

2. **Unit Tests** (Parallel)
   - Python unit tests (pytest)
   - dbt model tests

3. **Infrastructure Validation** (Parallel)
   - Terraform plan (detects resource changes)
   - dbt parser (validates models)

4. **Build Artifacts**
   - Docker image build and push (optional)

**Total CI Time**: ~5 minutes

### CD Workflow (`.github/workflows/deploy.yml`)

Triggered manually for deployment:

1. **Pre-deployment Checks**
   - Branch verification
   - Credential validation

2. **Infrastructure Setup** → dbt Models → Docker Images → Integration Tests

3. **Environment-specific Deployment**
   - `dev`: Immediate deployment
   - `staging`: Code review approval required
   - `prod`: Manual approval + Slack notification

---

## 📈 Data Models

### Staging Models (Dimensional Views)

| Model | Description | Rows | Columns |
|-------|-------------|------|---------|
| `dim_order` | Order details with items and profit | 631,301 | 18 |
| `dim_customer` | Customer demographics and location | ~2,500 | 10 |
| `dim_location` | Geographic information | ~1,000 | 8 |
| `dim_product` | Product catalog and categories | ~500 | 6 |
| `dim_department` | Department and sales info | ~5 | 4 |
| `dim_shipping` | Shipping and delivery metrics | 631,301 | 12 |

### Mart Models (Analytical Tables)

| Mart | Purpose | Update Frequency | Users |
|------|---------|------------------|-------|
| `overall_performance` | Monthly KPIs (sales, profit, shipping) | Daily | Executives |
| `inventory_levels` | Inventory aging and turnover analysis | Weekly | Supply Chain |
| `customer_retention_rate` | Monthly customer retention metrics | Daily | Marketing |
| `financial_commitments` | Department-product financial analysis | Weekly | Finance |
| `fraud_detection` | High-value customer anomalies | Real-time | Risk |
| `payment_delays` | Shipping delays and delivery status | Daily | Operations |

---

## 📊 Data Exploration

### Jupyter Notebook
```bash
# Open data exploration notebook
jupyter notebook data/data_exploration.ipynb
```

The notebook includes:
- Data loading and encoding detection
- Duplicate detection analysis
- Data type profiling
- Numeric range analysis
- Categorical value analysis
- Missing value investigation
- Data quality summary

### CLI Tool
```bash
# Interactive data exploration
python data/data_view.py
```

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [CI_CD_STRATEGY.md](CI_CD_STRATEGY.md) | Comprehensive CI/CD architecture and implementation |
| [CI_CD_QUICKSTART.md](CI_CD_QUICKSTART.md) | Quick setup guide for CI/CD pipelines |
| [note/DATA_PIPELINE_FLOW.md](note/DATA_PIPELINE_FLOW.md) | Data flow diagrams and architecture |
| [note/BATCH_DATA_PROCESSING.md](note/BATCH_DATA_PROCESSING.md) | Batch ETL pipeline details |
| [note/STREAMING_PIPELINE_GUIDE.md](note/STREAMING_PIPELINE_GUIDE.md) | Kafka streaming setup |
| [note/TERRAFORM_GUIDE.md](note/TERRAFORM_GUIDE.md) | Infrastructure provisioning |
| [dbt/dbt_pipeline.md](dbt/dbt_pipeline.md) | dbt model architecture |
| [dbt/SOURCE_AND_DEDUPLICATION_GUIDE.md](dbt/SOURCE_AND_DEDUPLICATION_GUIDE.md) | Data deduplication strategy |

---

## 🔑 Key Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Streaming** | Apache Kafka | 7.4.0 | Real-time data ingestion |
| **Processing** | Apache Spark | 4.1.1 | Batch data transformation |
| **Data Warehouse** | Google BigQuery | Latest | Columnar data storage |
| **Cloud Storage** | Google Cloud Storage | Latest | Data lake (Bronze/Silver) |
| **Data Modeling** | dbt | 1.8.2 | SQL-based transformations |
| **Python** | Python | 3.11.14 | Data processing logic |
| **IaC** | Terraform | Latest | Infrastructure provisioning |
| **Containers** | Docker & Docker Compose | Latest | Service containerization |
| **Orchestration** | Airflow | Latest | Workflow scheduling (optional) |
| **CI/CD** | GitHub Actions | Latest | Automated testing & deployment |

---

## 🛠️ Troubleshooting

### Kafka Connection Issues
```bash
# Check if Kafka is running
docker ps | grep kafka

# View Kafka logs
docker logs <kafka-container-id>

# Test connection
nc -zv localhost 9092
```

### Spark Memory Errors
```bash
# Increase Spark memory allocation
export SPARK_DRIVER_MEMORY=4g
export SPARK_EXECUTOR_MEMORY=4g
```

### BigQuery Credentials
```bash
# Verify GCP credentials
gcloud auth application-default print-access-token

# Set credentials path
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/keys/gcp-cred.json"
```

### dbt Model Failures
```bash
# Validate dbt project structure
dbt parse

# Debug model execution
dbt run --debug

# Check model dependencies
dbt dag
```

---

## 📝 Environment Variables

Create a `.env` file in the project root:

```bash
# GCP Configuration
GCP_PROJECT_ID=stellar-stream-485314
GCS_BUCKET=supply-chain-data-bucket-485314
GOOGLE_APPLICATION_CREDENTIALS=/path/to/gcp-cred.json

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC=supply_chain_data

# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=supply_chain
POSTGRES_USER=admin
POSTGRES_PASSWORD=password

# Spark Configuration
SPARK_MASTER=local[*]
SPARK_DRIVER_MEMORY=4g
SPARK_EXECUTOR_MEMORY=4g

# Environment
ENVIRONMENT=dev  # dev, staging, prod
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Make** your changes
4. **Commit** with clear messages (`git commit -m 'Add amazing feature'`)
5. **Push** to the branch (`git push origin feature/amazing-feature`)
6. **Open** a Pull Request

### Code Standards
- Python: Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) (enforced by Black)
- SQL: Use lower_case_with_underscores for identifiers
- dbt: Follow dbt [style guide](https://docs.getdbt.com/guides/best-practices/how-we-style/styling-guide-overview)
- Commits: Use [conventional commits](https://www.conventionalcommits.org/)

---

## 📄 License

This project is licensed under the [MIT License](LICENSE) - see the LICENSE file for details.

---

## 👥 Authors

- **Celine Li** - Data Engineer
- *Project started*: February 2026
- *Last updated*: February 2026

---

## 🙏 Acknowledgments

- Apache Kafka & Spark communities
- Google Cloud Platform documentation
- dbt Labs and community
- Contributors and reviewers

---

## 📞 Support

For issues, questions, or suggestions:

1. **GitHub Issues**: [Create an issue](https://github.com/CelineLQZ/real-time-supply-chain-data-engineering/issues)
2. **Documentation**: Check [docs](note/) directory
3. **Email**: Submit questions with reproducible examples

---

<div align="center">

**[⬆ back to top](#real-time-supply-chain-data-engineering-platform)**

Made with ❤️ by Celine Li | Star ⭐ if you find this project helpful!

</div>
