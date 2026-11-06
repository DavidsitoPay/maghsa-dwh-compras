DROP TABLE IF EXISTS hechos_compras;
CREATE EXTERNAL TABLE hechos_compras (id_compra STRING, fecha_id STRING, proveedor_id STRING, producto_id STRING, categoria_id STRING, unidad_organizacional_id STRING, cantidad DOUBLE, precio_unitario DOUBLE, monto_total DOUBLE, moneda STRING, condicion_pago STRING, lead_time_dias INT) PARTITIONED BY (anio STRING, mes STRING) STORED AS PARQUET LOCATION '<location_hechos>' TBLPROPERTIES ('parquet.compression'='SNAPPY');
MSCK REPAIR TABLE hechos_compras;
