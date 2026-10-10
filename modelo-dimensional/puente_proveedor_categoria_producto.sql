-- ============================================================
-- Tabla puente (N:M): puente_proveedor_categoria_producto
-- Qué categorías de producto suministra realmente cada proveedor
-- (subconjunto de lo permitido por categoria_proveedor_x_categoria_producto
-- según las categorías de proveedor que tenga asignadas).
-- ============================================================

CREATE EXTERNAL TABLE IF NOT EXISTS compras_dwh.puente_proveedor_categoria_producto (
    proveedor_id  STRING,   -- FK -> dim_proveedor.proveedor_id
    categoria_id  STRING    -- FK -> dim_categoria.categoria_id
)
STORED AS PARQUET
LOCATION 's3://<bucket-maghsa-dwh>/analytics/puente_proveedor_categoria_producto/'
TBLPROPERTIES ('parquet.compression'='SNAPPY');
