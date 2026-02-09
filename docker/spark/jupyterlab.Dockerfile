FROM cluster-base

# -- Layer: JupyterLab

ARG spark_version=3.5.0
ARG jupyterlab_version=3.6.1

RUN apt-get update -y && \
    apt-get install -y python3-pip && \
    pip3 install --break-system-packages wget pyspark==${spark_version} jupyterlab==${jupyterlab_version}

# 复制 GCS 连接器 JAR 到 PySpark jars 目录，支持 gs:// 读写
COPY jar_files/gcs-connector-hadoop3-2.2.5.jar /usr/local/lib/python3.12/dist-packages/pyspark/jars/

# -- Runtime

EXPOSE 8888
WORKDIR ${SHARED_WORKSPACE}
CMD jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --NotebookApp.token=