-- ============================================================
-- Tabla puente (N:M): puente_proveedor_producto
-- Qué productos específicos suministra cada proveedor. No repite
-- categoria_id aquí a propósito: ese dato ya vive en
-- dim_producto.categoria_id, y duplicarlo permitiría que ambos
-- valores se desincronizaran. La validación de que el producto
-- pertenezca a una categoría permitida para el proveedor se hace en
-- la aplicación (Lambda), no en esta tabla.
-- ============================================================

CREATE EXTERNAL TABLE IF NOT EXISTS compras_dwh.puente_proveedor_producto (
    proveedor_id  STRING,   -- FK -> dim_proveedor.proveedor_id
    producto_id   STRING    -- FK -> dim_producto.producto_id
)
STORED AS PARQUET
LOCATION 's3://<bucket-maghsa-dwh>/analytics/puente_proveedor_producto/'
TBLPROPERTIES ('parquet.compression'='SNAPPY');
