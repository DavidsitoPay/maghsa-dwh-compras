DROP TABLE IF EXISTS tmp_csv_categorias_proveedor;
CREATE EXTERNAL TABLE tmp_csv_categorias_proveedor (`categoria_proveedor_id` string, `nombre` string, `descripcion` string) ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde' LOCATION 's3://<bucket-maghsa-dwh>/raw/categorias_proveedor/' TBLPROPERTIES ('skip.header.line.count'='1');
DROP TABLE IF EXISTS tmp_a_categorias_proveedor;
CREATE TABLE tmp_a_categorias_proveedor WITH (format='PARQUET', parquet_compression='SNAPPY', external_location='s3://<bucket-maghsa-dwh>/analytics/dim_categoria_proveedor/') AS SELECT categoria_proveedor_id, nombre, descripcion FROM tmp_csv_categorias_proveedor;
DROP TABLE tmp_a_categorias_proveedor;
DROP TABLE IF EXISTS tmp_c_categorias_proveedor;
CREATE TABLE tmp_c_categorias_proveedor WITH (format='PARQUET', parquet_compression='SNAPPY', external_location='s3://<bucket-maghsa-dwh>/curated/categorias_proveedor/') AS SELECT categoria_proveedor_id, nombre, descripcion FROM tmp_csv_categorias_proveedor;
DROP TABLE tmp_c_categorias_proveedor;
DROP TABLE tmp_csv_categorias_proveedor;
