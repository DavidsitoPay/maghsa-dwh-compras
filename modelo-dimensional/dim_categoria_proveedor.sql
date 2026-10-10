-- ============================================================
-- Dimensión: dim_categoria_proveedor
-- ============================================================

CREATE EXTERNAL TABLE IF NOT EXISTS compras_dwh.dim_categoria_proveedor (
    categoria_proveedor_id STRING,
    nombre                  STRING,
    descripcion             STRING
)
STORED AS PARQUET
LOCATION 's3://<bucket-maghsa-dwh>/analytics/dim_categoria_proveedor/'
TBLPROPERTIES ('parquet.compression'='SNAPPY');
