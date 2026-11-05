# Organización lógica del almacenamiento en S3

Organización por zonas (raw / curated / analytics), alineada al ciclo de madurez del dato
descrito en el marco teórico del documento (arquitectura por capas).

- `raw/` recibe los CSV de origen: la carga manual de `sample-data/` y lo que escribe el
  formulario de captura (`lambda-captura/`).
- `curated/` y `analytics/` los genera `athena/etl/` (CTAS desde `raw/`).

```
s3://<bucket-maghsa-dwh>/
├── raw/                          # Datos originales, sin transformar (CSV tal cual llegan)
│   ├── compras/
│   │   └── anio=AAAA/mes=MM/registro_compras.csv
│   ├── compras_web/
│   │   └── registro_compras_web.csv    # lo crea el formulario con la primera compra registrada; sin anio=/mes=
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
│   ├── compras/anio=AAAA/mes=MM/*.parquet
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
├── athena-results/              # Resultados de consultas Athena; expiran a los 30 días (regla de ciclo de vida)
└── analytics/                    # Modelo dimensional listo para consumo (Athena / Power BI)
    ├── hechos_compras/anio=AAAA/mes=MM/*.parquet
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

`raw/compras/` guarda el histórico por partición `anio=`/`mes=`. `raw/compras_web/` guarda las
compras capturadas por el formulario en un solo archivo (`OCW####`), fuera de esa jerarquía; la Lambda crea el archivo y su prefijo con la primera compra capturada; la
carga las une al histórico y las particiona por su `fecha`.

Las tablas `puente_*` y `categoria_proveedor_x_categoria_producto` son relaciones N:M o de
regla de negocio, no dimensiones tradicionales — ver `/modelo-dimensional/README.md` para el
detalle de por qué existen separadas de `dim_proveedor`.

## Criterios de diseño

- **Particionamiento:** `hechos_compras` y `curated/compras/` se particionan por `anio`/`mes`
  (derivados de la fecha de la compra) para que Athena escanee solo los datos relevantes por
  consulta y reduzca costo de procesamiento.
- **Formato:** `raw/` se mantiene en CSV (formato de origen); `curated/` y `analytics/` migran a
  Parquet + compresión Snappy, más eficiente para consultas columnar en Athena.
- **Nomenclatura:** prefijos en minúsculas, particiones estilo Hive (`anio=AAAA/mes=MM/`) para que
  el crawler y `MSCK REPAIR TABLE` las reconozcan automáticamente; la carga oficial ejecuta
  `MSCK REPAIR TABLE hechos_compras` al terminar.
- **Ciclo de vida:** la regla `expirar-athena-results-30d` (habilitada) hace expirar a los 30 días
  los objetos bajo `athena-results/`, que guarda los resultados de consultas Athena: subprefijos
  `powerbi/` (workgroup `maghsa-powerbi`), `etl/` y `tables/` (resultados de CTAS/ETL).
  La regla `abortar-multipart-7d` (todo el bucket, sin expiración de objetos) aborta las cargas multiparte incompletas a los 7 días.
  No hay reglas de expiración sobre `raw/`, `curated/` ni `analytics/`; la única regla que alcanza todo el bucket es `abortar-multipart-7d`. Es una cuenta personal de pruebas con
  objetivo de gasto ~0: no hay nada programado; el crawler `crawler-maghsa-compras-analytics` no
  tiene schedule y se ejecuta a mano, y no hay triggers de Glue ni reglas de EventBridge o
  EventBridge Scheduler.
- **Seguridad del bucket de datos:** cifrado SSE-S3 (AES256); versionado deshabilitado.

## Bucket de prueba (capa gratuita)

Para la evidencia funcional se puede usar un bucket único con esta misma estructura de prefijos
(no hace falta un bucket por zona). El nombre real del bucket sustituye a `<bucket-maghsa-dwh>`
en los scripts de `/modelo-dimensional/` y `/glue/`.
