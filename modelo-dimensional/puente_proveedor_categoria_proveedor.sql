-- ============================================================
-- Tabla puente (N:M): puente_proveedor_categoria_proveedor
-- A qué categoría(s) de proveedor pertenece cada proveedor.
-- Ej.: un proveedor puede ser "Repuestos" y "Combustibles" a la vez.
-- ============================================================

CREATE EXTERNAL TABLE IF NOT EXISTS compras_dwh.puente_proveedor_categoria_proveedor (
    proveedor_id            STRING,   -- FK -> dim_proveedor.proveedor_id
    categoria_proveedor_id  STRING    -- FK -> dim_categoria_proveedor.categoria_proveedor_id
)
STORED AS PARQUET
LOCATION 's3://<bucket-maghsa-dwh>/analytics/puente_proveedor_categoria_proveedor/'
TBLPROPERTIES ('parquet.compression'='SNAPPY');
