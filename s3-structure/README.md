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
│   ├── categorias/catalogo_categorias.csv
│   ├── categorias_proveedor/categorias_proveedor.csv
│   ├── unidades_organizacionales/unidades_organizacionales.csv
│   ├── proveedor_categoria_proveedor/proveedor_categoria_proveedor.csv
│   ├── categoria_proveedor_x_categoria_producto/categoria_proveedor_x_categoria_producto.csv
│   ├── proveedor_categoria_producto/proveedor_categoria_producto.csv
│   ├── proveedor_x_producto/proveedor_x_producto.csv
│   └── contacto_proveedor/contacto_proveedor.csv
│
├── curated/                      # Datos validados/depurados, aún desnormalizados
│   ├── compras/anio=2026/mes=08/*.parquet
│   ├── proveedores/*.parquet
│   ├── productos/*.parquet
│   ├── categorias/*.parquet
│   ├── categorias_proveedor/*.parquet
│   ├── unidades_organizacionales/*.parquet
│   ├── proveedor_categoria_proveedor/*.parquet
│   ├── categoria_proveedor_x_categoria_producto/*.parquet
│   ├── proveedor_categoria_producto/*.parquet
│   ├── proveedor_x_producto/*.parquet
│   └── contacto_proveedor/*.parquet
│
└── analytics/                    # Modelo dimensional listo para consumo (Athena / Power BI)
    ├── hechos_compras/anio=2026/mes=08/*.parquet
    ├── dim_proveedor/*.parquet
    ├── dim_producto/*.parquet
    ├── dim_categoria/*.parquet
    ├── dim_tiempo/*.parquet
    ├── dim_categoria_proveedor/*.parquet
    ├── dim_unidad_organizacional/*.parquet
    ├── puente_proveedor_categoria_proveedor/*.parquet
    ├── categoria_proveedor_x_categoria_producto/*.parquet
    ├── puente_proveedor_categoria_producto/*.parquet
    ├── puente_proveedor_producto/*.parquet
    └── dim_contacto_proveedor/*.parquet
```

Las tablas `puente_*` y `categoria_proveedor_x_categoria_producto` son relaciones N:M o de
regla de negocio, no dimensiones tradicionales — ver `/modelo-dimensional/README.md` para el
detalle de por qué existen separadas de `dim_proveedor`.

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
