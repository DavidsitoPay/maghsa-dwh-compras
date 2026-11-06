DROP TABLE IF EXISTS tmp_csv_contacto_proveedor;
CREATE EXTERNAL TABLE tmp_csv_contacto_proveedor (`proveedor_id` string, `nombre_contacto` string, `telefonos` string, `correos` string) ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde' LOCATION 's3://<bucket-maghsa-dwh>/raw/contacto_proveedor/' TBLPROPERTIES ('skip.header.line.count'='1');
DROP TABLE IF EXISTS tmp_a_contacto_proveedor;
CREATE TABLE tmp_a_contacto_proveedor WITH (format='PARQUET', parquet_compression='SNAPPY', external_location='s3://<bucket-maghsa-dwh>/analytics/runs/<run_id>/dim_contacto_proveedor/') AS SELECT proveedor_id, nombre_contacto, telefonos, correos FROM tmp_csv_contacto_proveedor;
DROP TABLE IF EXISTS tmp_c_contacto_proveedor;
CREATE TABLE tmp_c_contacto_proveedor WITH (format='PARQUET', parquet_compression='SNAPPY', external_location='s3://<bucket-maghsa-dwh>/curated/runs/<run_id>/contacto_proveedor/') AS SELECT proveedor_id, nombre_contacto, telefonos, correos FROM tmp_csv_contacto_proveedor;
DROP TABLE tmp_c_contacto_proveedor;
DROP TABLE tmp_csv_contacto_proveedor;
