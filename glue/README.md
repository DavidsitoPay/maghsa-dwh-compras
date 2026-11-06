# AWS Glue Data Catalog

El Glue Data Catalog es el metastore de Athena. La base `compras_dwh` y sus 12 tablas externas (una por tabla de `analytics/`) se definen ejecutando en Athena los DDL de `/modelo-dimensional/`. Cada tabla apunta con `LOCATION` a su prefijo `analytics/<tabla>/` del bucket de datos.

```sql
CREATE DATABASE IF NOT EXISTS compras_dwh;
```

Luego ejecutar en orden los `.sql` de `/modelo-dimensional/`.

## Carga de datos

La carga oficial es `athena/etl/` (CTAS desde `raw/`; el orden de ejecución está en su README). Escribe los Parquet en `curated/` y `analytics/`, y su último paso de hechos ejecuta `MSCK REPAIR TABLE hechos_compras`, así que el pipeline mantiene sincronizadas las particiones `anio`/`mes` del catálogo.

## Sincronizar particiones de hechos_compras

`hechos_compras` está particionada por `anio`/`mes`. Si se agregan objetos a `analytics/hechos_compras/` fuera de `athena/etl/`, hay que sincronizar el catálogo a mano:

```sql
MSCK REPAIR TABLE compras_dwh.hechos_compras;
```

## Validar

```sql
SHOW TABLES IN compras_dwh;
```
