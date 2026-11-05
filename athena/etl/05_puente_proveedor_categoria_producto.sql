DROP TABLE IF EXISTS tmp_csv_proveedor_categoria_producto;
CREATE EXTERNAL TABLE tmp_csv_proveedor_categoria_producto (`proveedor_id` string, `categoria_id` string) ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde' LOCATION 's3://<bucket-maghsa-dwh>/raw/proveedor_categoria_producto/' TBLPROPERTIES ('skip.header.line.count'='1');
DROP TABLE IF EXISTS tmp_a_proveedor_categoria_producto;
CREATE TABLE tmp_a_proveedor_categoria_producto WITH (format='PARQUET', parquet_compression='SNAPPY', external_location='s3://<bucket-maghsa-dwh>/analytics/puente_proveedor_categoria_producto/') AS SELECT proveedor_id, categoria_id FROM tmp_csv_proveedor_categoria_producto;
DROP TABLE tmp_a_proveedor_categoria_producto;
DROP TABLE IF EXISTS tmp_c_proveedor_categoria_producto;
CREATE TABLE tmp_c_proveedor_categoria_producto WITH (format='PARQUET', parquet_compression='SNAPPY', external_location='s3://<bucket-maghsa-dwh>/curated/proveedor_categoria_producto/') AS SELECT proveedor_id, categoria_id FROM tmp_csv_proveedor_categoria_producto;
DROP TABLE tmp_c_proveedor_categoria_producto;
DROP TABLE tmp_csv_proveedor_categoria_producto;
