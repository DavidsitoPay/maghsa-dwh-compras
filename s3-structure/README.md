# Organización lógica del almacenamiento en S3

Organización por zonas (raw / curated / analytics), alineada al ciclo de madurez del dato
descrito en el marco teórico del documento (arquitectura por capas).

- `raw/` recibe los CSV de origen: la carga manual de `sample-data/` y lo que escribe el
  formulario de captura (`lambda-captura/`).
- `curated/` y `analytics/` los genera `athena/etl/` (CTAS desde `raw/`), en prefijos `runs/<run_id>/` por corrida (ver «Corridas»).

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
│   └── etl/                     # Estado de la carga: lock.json, ultimo_run.json, previos_<run_id>.json
└── analytics/                    # Modelo dimensional listo para consumo (Athena / Power BI)
    ├── runs/<run_id>/<tabla>/*.parquet   # Publicación por corrida; las 12 tablas apuntan aquí
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
- **Nomenclatura:** prefijos en minúsculas, particiones estilo Hive (`anio=AAAA/mes=MM/`).
  `hechos_compras` resuelve sus particiones por partition projection, sin `MSCK REPAIR TABLE` (ver `glue/README.md`).
- **Ciclo de vida:** la regla `expirar-athena-results-30d` (habilitada) hace expirar a los 30 días
  los objetos bajo `athena-results/`, que guarda los resultados de consultas Athena: subprefijos
  `powerbi/` (workgroup `maghsa-powerbi`), `etl/` y `tables/` (resultados de CTAS/ETL).
  La regla `abortar-multipart-7d` (todo el bucket, sin expiración de objetos) aborta las cargas multiparte incompletas a los 7 días.
  No hay reglas de expiración sobre `raw/`, `curated/` ni `analytics/`; la única regla que alcanza todo el bucket es `abortar-multipart-7d`. Es una cuenta personal de pruebas con
  objetivo de gasto ~0. No hay triggers de Glue. Los Schedules de EventBridge Scheduler
  (`maghsa-carga-diaria` y `maghsa-purga-semanal`) existen en `DISABLED`: no programan nada hasta que se activen.
- **Seguridad del bucket de datos:** cifrado SSE-S3 (AES256); versionado deshabilitado; política de bucket
  `DenyInsecureTransport` (rechaza peticiones sin TLS).

## Corridas (`runs/`)

Cada corrida de la carga (`maghsa-carga-etl`) escribe `analytics/runs/<run_id>/<tabla>/` y
`curated/runs/<run_id>/<entidad>/`, con `<run_id>` = `yyyyMMddHHmmss` en UTC. Tras validar, las 12 tablas de
`compras_dwh` apuntan a su prefijo `runs/<run_id>/`. Los prefijos `analytics/<tabla>/` y `curated/<entidad>/`
sin `runs/` son el respaldo congelado: la carga no los escribe ni los borra.

La purga semanal (`maghsa-purga-runs`) borra los runs fuera de las 14 corridas más recientes, en `analytics/runs/`
y `curated/runs/`, protegiendo lo que referencia Glue y el estado. No toca `raw/`, `athena-results/` ni el legado.

`athena-results/etl/` guarda el estado: `lock.json` (lock de la carga), `ultimo_run.json` (corrida publicada) y
`previos_<run_id>.json` (ubicaciones anteriores, para revertir y para la purga). La regla de expiración de 30 días
de `athena-results/` también alcanza a `etl/`.

## Bucket de prueba (capa gratuita)

Para la evidencia funcional se puede usar un bucket único con esta misma estructura de prefijos
(no hace falta un bucket por zona). El nombre real del bucket sustituye a `<bucket-maghsa-dwh>`
en los scripts de `/modelo-dimensional/` y `/glue/`.
