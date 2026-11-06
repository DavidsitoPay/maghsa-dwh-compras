DROP TABLE IF EXISTS tmp_csv_productos;
CREATE EXTERNAL TABLE tmp_csv_productos (`producto_id` string, `nombre` string, `categoria_id` string, `unidad_medida` string, `descripcion` string) ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde' LOCATION 's3://<bucket-maghsa-dwh>/raw/productos/' TBLPROPERTIES ('skip.header.line.count'='1');
DROP TABLE IF EXISTS tmp_a_productos;
CREATE TABLE tmp_a_productos WITH (format='PARQUET', parquet_compression='SNAPPY', external_location='s3://<bucket-maghsa-dwh>/analytics/runs/<run_id>/dim_producto/') AS SELECT producto_id, nombre, categoria_id, unidad_medida, descripcion FROM tmp_csv_productos;
DROP TABLE IF EXISTS tmp_c_productos;
CREATE TABLE tmp_c_productos WITH (format='PARQUET', parquet_compression='SNAPPY', external_location='s3://<bucket-maghsa-dwh>/curated/runs/<run_id>/productos/') AS SELECT producto_id, nombre, categoria_id, unidad_medida, descripcion FROM tmp_csv_productos;
DROP TABLE tmp_c_productos;
DROP TABLE tmp_csv_productos;
