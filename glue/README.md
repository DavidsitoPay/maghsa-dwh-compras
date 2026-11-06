# AWS Glue Data Catalog

El Glue Data Catalog es el metastore de Athena. La base `compras_dwh` y sus 12 tablas externas (una por tabla de `analytics/`) se definen ejecutando en Athena los DDL de `/modelo-dimensional/`. Tras cada corrida de la carga, cada tabla apunta con `LOCATION` a su prefijo `analytics/runs/<run_id>/<tabla>/` del bucket de datos.

```sql
CREATE DATABASE IF NOT EXISTS compras_dwh;
```

Luego ejecutar en orden los `.sql` de `/modelo-dimensional/`.

## Carga de datos

La carga oficial es `athena/etl/` (CTAS desde `raw/`; el orden de ejecución está en su README), ejecutada por la Lambda `maghsa-carga-etl` (ver `lambda-carga/README.md`). Escribe los Parquet en `curated/runs/<run_id>/` y `analytics/runs/<run_id>/` y publica repuntando la `LOCATION` de las tablas.

## Particiones de hechos_compras

`hechos_compras` usa partition projection (`projection.enabled=true`; `anio` 2024–2035, `mes` 01–12 con dos dígitos): Athena calcula las particiones desde las propiedades de la tabla, sin registrarlas en el catálogo. Solo el modo de respaldo `recreate` de la carga usa `MSCK REPAIR TABLE`.

## Validar

```sql
SHOW TABLES IN compras_dwh;
```
