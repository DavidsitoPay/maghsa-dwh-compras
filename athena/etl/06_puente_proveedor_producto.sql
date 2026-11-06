DROP TABLE IF EXISTS tmp_csv_proveedor_x_producto;
CREATE EXTERNAL TABLE tmp_csv_proveedor_x_producto (`proveedor_id` string, `producto_id` string) ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde' LOCATION 's3://<bucket-maghsa-dwh>/raw/proveedor_x_producto/' TBLPROPERTIES ('skip.header.line.count'='1');
DROP TABLE IF EXISTS tmp_a_proveedor_x_producto;
CREATE TABLE tmp_a_proveedor_x_producto WITH (format='PARQUET', parquet_compression='SNAPPY', external_location='s3://<bucket-maghsa-dwh>/analytics/runs/<run_id>/puente_proveedor_producto/') AS SELECT proveedor_id, producto_id FROM tmp_csv_proveedor_x_producto;
DROP TABLE IF EXISTS tmp_c_proveedor_x_producto;
CREATE TABLE tmp_c_proveedor_x_producto WITH (format='PARQUET', parquet_compression='SNAPPY', external_location='s3://<bucket-maghsa-dwh>/curated/runs/<run_id>/proveedor_x_producto/') AS SELECT proveedor_id, producto_id FROM tmp_csv_proveedor_x_producto;
DROP TABLE tmp_c_proveedor_x_producto;
DROP TABLE tmp_csv_proveedor_x_producto;
