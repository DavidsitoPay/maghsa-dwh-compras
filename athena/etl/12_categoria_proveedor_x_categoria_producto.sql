DROP TABLE IF EXISTS tmp_csv_categoria_proveedor_x_categoria_producto;
CREATE EXTERNAL TABLE tmp_csv_categoria_proveedor_x_categoria_producto (`categoria_proveedor_id` string, `categoria_id` string) ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde' LOCATION 's3://<bucket-maghsa-dwh>/raw/categoria_proveedor_x_categoria_producto/' TBLPROPERTIES ('skip.header.line.count'='1');
DROP TABLE IF EXISTS tmp_a_categoria_proveedor_x_categoria_producto;
CREATE TABLE tmp_a_categoria_proveedor_x_categoria_producto WITH (format='PARQUET', parquet_compression='SNAPPY', external_location='s3://<bucket-maghsa-dwh>/analytics/categoria_proveedor_x_categoria_producto/') AS SELECT categoria_proveedor_id, categoria_id FROM tmp_csv_categoria_proveedor_x_categoria_producto;
DROP TABLE tmp_a_categoria_proveedor_x_categoria_producto;
DROP TABLE IF EXISTS tmp_c_categoria_proveedor_x_categoria_producto;
CREATE TABLE tmp_c_categoria_proveedor_x_categoria_producto WITH (format='PARQUET', parquet_compression='SNAPPY', external_location='s3://<bucket-maghsa-dwh>/curated/categoria_proveedor_x_categoria_producto/') AS SELECT categoria_proveedor_id, categoria_id FROM tmp_csv_categoria_proveedor_x_categoria_producto;
DROP TABLE tmp_c_categoria_proveedor_x_categoria_producto;
DROP TABLE tmp_csv_categoria_proveedor_x_categoria_producto;
