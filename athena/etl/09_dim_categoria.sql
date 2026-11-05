DROP TABLE IF EXISTS tmp_csv_categorias;
CREATE EXTERNAL TABLE tmp_csv_categorias (`categoria_id` string, `nombre_categoria` string, `familia_gasto` string) ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde' LOCATION 's3://<bucket-maghsa-dwh>/raw/categorias/' TBLPROPERTIES ('skip.header.line.count'='1');
DROP TABLE IF EXISTS tmp_a_categorias;
CREATE TABLE tmp_a_categorias WITH (format='PARQUET', parquet_compression='SNAPPY', external_location='s3://<bucket-maghsa-dwh>/analytics/dim_categoria/') AS SELECT categoria_id, nombre_categoria, familia_gasto FROM tmp_csv_categorias;
DROP TABLE tmp_a_categorias;
DROP TABLE IF EXISTS tmp_c_categorias;
CREATE TABLE tmp_c_categorias WITH (format='PARQUET', parquet_compression='SNAPPY', external_location='s3://<bucket-maghsa-dwh>/curated/categorias/') AS SELECT categoria_id, nombre_categoria, familia_gasto FROM tmp_csv_categorias;
DROP TABLE tmp_c_categorias;
DROP TABLE tmp_csv_categorias;
