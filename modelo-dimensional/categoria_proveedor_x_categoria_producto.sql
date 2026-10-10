-- ============================================================
-- Tabla de regla de negocio: categoria_proveedor_x_categoria_producto
-- Define qué categorías de producto son válidas para cada categoría
-- de proveedor. Se usa principalmente para filtrar el formulario de
-- ingesta (no es una tabla de hechos ni se une directamente a
-- hechos_compras); se mantiene en analytics/ solo para trazabilidad
-- y consulta desde Athena si se necesita auditar la regla.
-- ============================================================

CREATE EXTERNAL TABLE IF NOT EXISTS compras_dwh.categoria_proveedor_x_categoria_producto (
    categoria_proveedor_id STRING,   -- FK -> dim_categoria_proveedor.categoria_proveedor_id
    categoria_id            STRING    -- FK -> dim_categoria.categoria_id
)
STORED AS PARQUET
LOCATION 's3://<bucket-maghsa-dwh>/analytics/categoria_proveedor_x_categoria_producto/'
TBLPROPERTIES ('parquet.compression'='SNAPPY');
