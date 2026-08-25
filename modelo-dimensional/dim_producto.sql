-- ============================================================
-- Dimensión: dim_producto
-- ============================================================

CREATE EXTERNAL TABLE IF NOT EXISTS compras_dwh.dim_producto (
    producto_id     STRING,
    nombre          STRING,
    categoria_id    STRING,   -- FK -> dim_categoria.categoria_id
    unidad_medida   STRING,
    descripcion     STRING
)
STORED AS PARQUET
LOCATION 's3://<bucket-maghsa-dwh>/analytics/dim_producto/'
TBLPROPERTIES ('parquet.compression'='SNAPPY');
