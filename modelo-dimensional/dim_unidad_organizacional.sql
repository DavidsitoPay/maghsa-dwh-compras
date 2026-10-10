-- ============================================================
-- Dimensión: dim_unidad_organizacional
-- ============================================================

CREATE EXTERNAL TABLE IF NOT EXISTS compras_dwh.dim_unidad_organizacional (
    unidad_organizacional_id STRING,
    nombre                    STRING
)
STORED AS PARQUET
LOCATION 's3://<bucket-maghsa-dwh>/analytics/dim_unidad_organizacional/'
TBLPROPERTIES ('parquet.compression'='SNAPPY');
