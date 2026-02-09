# 运行步骤

1. 启动容器（如已启动可跳过）：
   - `docker compose -f docker/spark/docker-compose.yaml --env-file docker/spark/.env up -d`

2. 确保 BigQuery 客户端已安装（如已安装可跳过）：
   - `docker exec supply-chain-jupyterlab pip install --break-system-packages google-cloud-bigquery`

3. 运行导入脚本：
   - `docker exec -e PYTHONPATH=/opt/workspace supply-chain-jupyterlab python /opt/workspace/batch_pipeline/bigquery/load_to_bigquery.py`
