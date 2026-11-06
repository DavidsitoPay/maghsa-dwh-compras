DROP TABLE IF EXISTS tmp_csv_proveedores;
CREATE EXTERNAL TABLE tmp_csv_proveedores (`proveedor_id` string, `nombre` string, `pais` string, `localizacion` string, `condiciones_pago` string, `estado` string) ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde' LOCATION 's3://<bucket-maghsa-dwh>/raw/proveedores/' TBLPROPERTIES ('skip.header.line.count'='1');
DROP TABLE IF EXISTS tmp_a_proveedores;
CREATE TABLE tmp_a_proveedores WITH (format='PARQUET', parquet_compression='SNAPPY', external_location='s3://<bucket-maghsa-dwh>/analytics/runs/<run_id>/dim_proveedor/') AS SELECT proveedor_id, nombre, pais, localizacion, condiciones_pago, estado FROM tmp_csv_proveedores;
DROP TABLE IF EXISTS tmp_c_proveedores;
CREATE TABLE tmp_c_proveedores WITH (format='PARQUET', parquet_compression='SNAPPY', external_location='s3://<bucket-maghsa-dwh>/curated/runs/<run_id>/proveedores/') AS SELECT proveedor_id, nombre, pais, localizacion, condiciones_pago, estado FROM tmp_csv_proveedores;
DROP TABLE tmp_c_proveedores;
DROP TABLE tmp_csv_proveedores;
