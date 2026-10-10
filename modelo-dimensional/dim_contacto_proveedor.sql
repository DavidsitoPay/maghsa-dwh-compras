-- ============================================================
-- Dimensión: dim_contacto_proveedor
-- Dato operativo de consulta puntual (a quién llamar/escribir), no
-- se usa para agregaciones de monto. Sin normalizar teléfono/correo
-- a nivel individual: se guardan separados por coma cuando hay más
-- de uno, porque en la práctica cada contacto suele tener solo uno.
-- ============================================================

CREATE EXTERNAL TABLE IF NOT EXISTS compras_dwh.dim_contacto_proveedor (
    proveedor_id     STRING,   -- FK -> dim_proveedor.proveedor_id
    nombre_contacto  STRING,
    telefonos        STRING,
    correos          STRING
)
STORED AS PARQUET
LOCATION 's3://<bucket-maghsa-dwh>/analytics/dim_contacto_proveedor/'
TBLPROPERTIES ('parquet.compression'='SNAPPY');
