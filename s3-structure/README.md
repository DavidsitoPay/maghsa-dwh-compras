# Organización lógica del almacenamiento en S3

Se propone una organización por zonas (raw / curated / analytics), alineada al ciclo de
madurez del dato descrito en el marco teórico del documento (arquitectura por capas).

```
s3://<bucket-maghsa-dwh>/
├── raw/                          # Datos originales, sin transformar (CSV tal cual llegan)
│   ├── compras/
│   │   └── anio=2026/mes=08/registro_compras.csv
│   ├── proveedores/maestro_proveedores.csv
│   ├── productos/maestro_productos.csv
│   └── categorias/catalogo_categorias.csv
│
├── curated/                      # Datos validados/depurados, aún desnormalizados
│   ├── compras/anio=2026/mes=08/*.parquet
│   ├── proveedores/*.parquet
│   ├── productos/*.parquet
│   └── categorias/*.parquet
│
└── analytics/                    # Modelo dimensional listo para consumo (Athena / Power BI)
    ├── hechos_compras/anio=2026/mes=08/*.parquet
    ├── dim_proveedor/*.parquet
    ├── dim_producto/*.parquet
    ├── dim_categoria/*.parquet
    └── dim_tiempo/*.parquet
```

## Criterios de diseño

- **Particionamiento:** `hechos_compras` se particiona por `anio`/`mes` para que Athena escanee
  solo los datos relevantes por consulta y reduzca costo de procesamiento.
- **Formato:** `raw/` se mantiene en CSV (formato de origen); `curated/` y `analytics/` migran a
  Parquet + compresión Snappy, más eficiente para consultas columnar en Athena.
- **Nomenclatura:** prefijos en minúsculas, particiones estilo Hive (`anio=2026/mes=08/`) para que
  el crawler y `MSCK REPAIR TABLE` las reconozcan automáticamente.
- **Ciclo de vida:** se puede aplicar una política de lifecycle en `raw/` (ej. mover a S3
  Infrequent Access después de 90 días) para mantener el costo bajo, aunque para el alcance
  académico del proyecto no es indispensable en esta fase.

## Bucket de prueba (capa gratuita)

Para la evidencia funcional se puede usar un bucket único con esta misma estructura de prefijos
(no hace falta un bucket por zona). El nombre real del bucket sustituye a `<bucket-maghsa-dwh>`
en los scripts de `/modelo-dimensional/` y `/glue/`.
