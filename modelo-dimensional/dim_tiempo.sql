-- ============================================================
-- Dimensión: dim_tiempo
-- Se puede generar con un script (Python/SQL) para un rango de fechas
-- ============================================================

CREATE EXTERNAL TABLE IF NOT EXISTS compras_dwh.dim_tiempo (
    fecha_id     STRING,   -- yyyyMMdd
    fecha        DATE,
    anio         INT,
    trimestre    INT,
    mes          INT,
    nombre_mes   STRING,
    dia          INT,
    dia_semana   STRING
)
STORED AS PARQUET
LOCATION 's3://<bucket-maghsa-dwh>/analytics/dim_tiempo/'
TBLPROPERTIES ('parquet.compression'='SNAPPY');
