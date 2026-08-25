-- ============================================================
-- Tabla de hechos: hechos_compras
-- Grano: una fila por línea de orden de compra
-- Motor: Amazon Athena (tabla externa sobre S3, capa analytics/)
-- ============================================================

CREATE EXTERNAL TABLE IF NOT EXISTS compras_dwh.hechos_compras (
    id_compra          STRING,
    fecha_id           STRING,   -- FK -> dim_tiempo.fecha_id (formato yyyyMMdd)
    proveedor_id        STRING,   -- FK -> dim_proveedor.proveedor_id
    producto_id          STRING,   -- FK -> dim_producto.producto_id
    categoria_id        STRING,   -- FK -> dim_categoria.categoria_id
    unidad_organizacional STRING,
    cantidad            DOUBLE,
    precio_unitario     DOUBLE,
    monto_total         DOUBLE,
    moneda              STRING,
    condicion_pago      STRING,
    lead_time_dias      INT
)
PARTITIONED BY (anio STRING, mes STRING)
STORED AS PARQUET
LOCATION 's3://<bucket-maghsa-dwh>/analytics/hechos_compras/'
TBLPROPERTIES ('parquet.compression'='SNAPPY');

-- Después de cargar particiones nuevas, sincronizar el catálogo:
-- MSCK REPAIR TABLE compras_dwh.hechos_compras;
