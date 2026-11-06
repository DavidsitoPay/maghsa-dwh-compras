DROP TABLE IF EXISTS tmp_csv_unidades_organizacionales;
CREATE EXTERNAL TABLE tmp_csv_unidades_organizacionales (`unidad_organizacional_id` string, `nombre` string) ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde' LOCATION 's3://<bucket-maghsa-dwh>/raw/unidades_organizacionales/' TBLPROPERTIES ('skip.header.line.count'='1');
DROP TABLE IF EXISTS tmp_a_unidades_organizacionales;
CREATE TABLE tmp_a_unidades_organizacionales WITH (format='PARQUET', parquet_compression='SNAPPY', external_location='s3://<bucket-maghsa-dwh>/analytics/runs/<run_id>/dim_unidad_organizacional/') AS SELECT unidad_organizacional_id, nombre FROM tmp_csv_unidades_organizacionales;
DROP TABLE IF EXISTS tmp_c_unidades_organizacionales;
CREATE TABLE tmp_c_unidades_organizacionales WITH (format='PARQUET', parquet_compression='SNAPPY', external_location='s3://<bucket-maghsa-dwh>/curated/runs/<run_id>/unidades_organizacionales/') AS SELECT unidad_organizacional_id, nombre FROM tmp_csv_unidades_organizacionales;
DROP TABLE tmp_c_unidades_organizacionales;
DROP TABLE tmp_csv_unidades_organizacionales;
