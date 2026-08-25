-- ============================================================
-- Dimensión: dim_categoria
-- ============================================================

CREATE EXTERNAL TABLE IF NOT EXISTS compras_dwh.dim_categoria (
    categoria_id     STRING,
    nombre_categoria STRING,
    familia_gasto    STRING
)
STORED AS PARQUET
LOCATION 's3://<bucket-maghsa-dwh>/analytics/dim_categoria/'
TBLPROPERTIES ('parquet.compression'='SNAPPY');
