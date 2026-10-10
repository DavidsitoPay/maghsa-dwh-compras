-- ============================================================
-- Dimensión: dim_proveedor
-- ============================================================
-- categoria_proveedor se removió de esta tabla: un proveedor puede
-- pertenecer a más de una categoría, por lo que la relación vive en
-- puente_proveedor_categoria_proveedor (ver ese archivo).

CREATE EXTERNAL TABLE IF NOT EXISTS compras_dwh.dim_proveedor (
    proveedor_id        STRING,
    nombre              STRING,
    pais                STRING,
    localizacion        STRING,
    condiciones_pago    STRING,
    estado              STRING   -- vigente / inactivo
)
STORED AS PARQUET
LOCATION 's3://<bucket-maghsa-dwh>/analytics/dim_proveedor/'
TBLPROPERTIES ('parquet.compression'='SNAPPY');
