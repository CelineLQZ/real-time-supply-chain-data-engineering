import pyspark
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, row_number
from pyspark.sql.window import Window
from pyspark.sql.types import StructType
from config import credentials_path, jar_file_path, gcs_bucket_path, input_path, output_path, GCP_PROJECT_ID, partition_count
from utilis import customer_columns, product_columns, location_columns, order_columns, shipping_columns, department_columns, metadata_columns, column_name_mapping

# Create Spark Session with configuration
spark = SparkSession.builder \
    .appName('supply-chain-batch-pipeline') \
    .config("spark.jars", jar_file_path) \
    .config("spark.hadoop.fs.AbstractFileSystem.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFS") \
    .config("spark.hadoop.fs.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem") \
    .config("spark.hadoop.google.cloud.auth.service.account.enable", "true") \
    .config("spark.hadoop.google.cloud.auth.service.account.json.keyfile", credentials_path) \
    .config("spark.hadoop.google.cloud.project.id", GCP_PROJECT_ID) \
    .getOrCreate()

# Hadoop configuration for GCS access
hadoop_conf = spark._jsc.hadoopConfiguration()
hadoop_conf.set("fs.AbstractFileSystem.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFS")
hadoop_conf.set("fs.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem")
hadoop_conf.set("fs.gs.auth.service.account.json.keyfile", credentials_path)
hadoop_conf.set("fs.gs.auth.service.account.enable", "true")

# Helper to validate GCS input path
def assert_gcs_path_has_files(spark_session, gcs_path):
    jvm = spark_session._jvm
    hadoop_conf = spark_session._jsc.hadoopConfiguration()
    path = jvm.org.apache.hadoop.fs.Path(gcs_path)
    fs = path.getFileSystem(hadoop_conf)
    if not fs.exists(path):
        raise FileNotFoundError(f"GCS 路径不存在：{gcs_path}")
    statuses = fs.listStatus(path)
    if statuses is None or len(statuses) == 0:
        raise FileNotFoundError(f"GCS 路径为空（无任何文件）：{gcs_path}")

# Load data from GCS bucket
print(f'Loading Data from GCS Bucket path {input_path}')
assert_gcs_path_has_files(spark, input_path)
df_raw = spark.read.parquet(input_path + '*')
print('Done')
print(f'📊 原始数据列数：{len(df_raw.columns)}')
print(f'📋 原始数据所有列名：{df_raw.columns}')

# Function to extract specific columns from DataFrame
def extract_columns(df, columns_to_extract):
    # 直接选择列（不需要 col("data")，因为数据是平面结构）
    available_cols = [col_name for col_name in columns_to_extract if col_name in df.columns]
    missing_cols = [col_name for col_name in columns_to_extract if col_name not in df.columns]
    if missing_cols:
        print(f"⚠️  缺失的列：{missing_cols}")
    if not available_cols:
        print(f"⚠️  警告：请求的列不在 DataFrame 中。可用列：{df.columns}")
        return df.sparkSession.createDataFrame([], schema=StructType([]))  # 返回空 DataFrame（无列）
    return df.select(*available_cols)

# Function to standardize column names (replace spaces with underscores)
def standardize_column_names(df, original_columns):
    """将列名标准化：空格 -> 下划线，并返回标准化后的 DataFrame"""
    result_df = df
    for original_name in original_columns:
        if original_name in df.columns:
            standardized_name = column_name_mapping.get(original_name, original_name)
            if original_name != standardized_name:
                result_df = result_df.withColumnRenamed(original_name, standardized_name)
    return result_df

# Function to deduplicate dataframe by primary key
def deduplicate_by_key(df, primary_key_col):
    """使用 ROW_NUMBER 按主键去重，保留每个主键的第一条记录"""
    if primary_key_col not in df.columns:
        print(f"⚠️  警告：主键列 {primary_key_col} 不在 DataFrame 中，跳过去重")
        return df
    
    window = Window.partitionBy(primary_key_col).orderBy(primary_key_col)
    df_with_rn = df.withColumn("_rn", row_number().over(window))
    return df_with_rn.filter(col("_rn") == 1).drop("_rn")

# Function to create dimension tables
def create_dimension_tables(df, extract_func, columns_to_extract, table_name):
    dimension_df = extract_func(df, columns_to_extract)
    # Uncomment the line below if you want to create a temporary view for SQL queries
    # dimension_df.createOrReplaceTempView(table_name)
    return dimension_df

# Create dimension tables with standardized names and deduplication
customer_dimension = standardize_column_names(
    deduplicate_by_key(create_dimension_tables(df_raw, extract_columns, customer_columns, "customer_dimension"), "Customer_Id"),
    customer_columns
)
print('✅ Created Dimension table for Customers (standardized names, deduplicated)')

product_dimension = standardize_column_names(
    deduplicate_by_key(create_dimension_tables(df_raw, extract_columns, product_columns, "product_dimension"), "Product_Card_Id"),
    product_columns
)
print('✅ Created Dimension table for Products (standardized names, deduplicated)')

location_dimension = standardize_column_names(
    deduplicate_by_key(create_dimension_tables(df_raw, extract_columns, location_columns, "location_dimension"), "Order_Zipcode"),
    location_columns
)
print('✅ Created Dimension table for Location (standardized names, deduplicated)')

order_fact = standardize_column_names(
    deduplicate_by_key(create_dimension_tables(df_raw, extract_columns, order_columns, "order_fact"), "Order_Id"),
    order_columns
)
print(f'✅ Created Dimension table for Orders (standardized names, deduplicated)')
print(f'   → Order Fact 列数：{len(order_fact.columns)}')
print(f'   → Order Fact 列名：{order_fact.columns}')

shipping_dimension = standardize_column_names(
    deduplicate_by_key(create_dimension_tables(df_raw, extract_columns, shipping_columns, "shipping_dimension"), "Shipping_date"),
    shipping_columns
)
print('✅ Created Dimension table for Shipping (standardized names, deduplicated)')

department_dimension = standardize_column_names(
    deduplicate_by_key(create_dimension_tables(df_raw, extract_columns, department_columns, "department_dimension"), "Department_Id"),
    department_columns
)
print('✅ Created Dimension table for Departments (standardized names, deduplicated)')

# Function to extract metadata columns
def extract_metadata(df, columns_to_extract):
    # 对 metadata 列进行解析（如果存在）
    available_cols = [col_name for col_name in columns_to_extract if col_name in df.columns]
    if not available_cols:
        print(f"⚠️  警告：元数据列不在 DataFrame 中")
        return df.sparkSession.createDataFrame([], schema=StructType([]))  # 返回空 DataFrame（无列）
    return df.select(*available_cols)

# Create metadata dimension table with deduplication
metadata_dimension = standardize_column_names(
    deduplicate_by_key(create_dimension_tables(df_raw, extract_metadata, metadata_columns, "metadata_dimension"), "key"),
    metadata_columns
)
print('✅ Created Dimension table for Metadata (standardized names, deduplicated)')

# Dictionary to hold all dimension tables
dataframes = {
    "customer_dimension": customer_dimension,
    "product_dimension": product_dimension,
    "location_dimension": location_dimension,
    "order_fact": order_fact,
    "shipping_dimension": shipping_dimension,
    "department_dimension": department_dimension,
    "metadata_dimension": metadata_dimension
}

# Function to write dimension tables to GCS
def write_to_gcs(dataframes, output_path):
    print('Starting to Export Dimension tables to GCS...')
    for name, dataframe in dataframes.items():
        if not dataframe.columns:
            print(f"⚠️  跳过 {name}（无可用列）")
            continue
        output_file = output_path + name
        target_df = dataframe.repartition(partition_count) if partition_count and partition_count > 0 else dataframe
        target_df.write.mode("overwrite").option("compression", "snappy").parquet(output_file)
        print(f"✅ Exported Dataframe {name} to GCS: {output_file}")
    print('All dimension tables exported successfully!')

# Write dimension tables to GCS
if __name__ == "__main__":
    try:
        write_to_gcs(dataframes, output_path)
        print('\n🎉 Pipeline completed successfully!')
    except Exception as e:
        print(f'❌ Error during pipeline execution: {str(e)}')
        raise
    finally:
        spark.stop()