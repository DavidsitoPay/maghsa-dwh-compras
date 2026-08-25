-- ============================================================
-- Dimensión: dim_proveedor
-- ============================================================

CREATE EXTERNAL TABLE IF NOT EXISTS compras_dwh.dim_proveedor (
    proveedor_id        STRING,
    nombre              STRING,
    categoria_proveedor STRING,
    pais                STRING,
    localizacion        STRING,
    condiciones_pago    STRING,
    estado              STRING   -- vigente / inactivo
)
STORED AS PARQUET
LOCATION 's3://<bucket-maghsa-dwh>/analytics/dim_proveedor/'
TBLPROPERTIES ('parquet.compression'='SNAPPY');
