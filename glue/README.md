# AWS Glue Data Catalog

La base `compras_dwh` y sus 12 tablas externas (una por tabla de `analytics/`) se registran en el Glue Data Catalog ejecutando en Athena los DDL de `/modelo-dimensional/`; Athena los cataloga sin necesidad de un crawler.

```sql
CREATE DATABASE IF NOT EXISTS compras_dwh;
```

Luego ejecutar en orden los `.sql` de `/modelo-dimensional/`.

## Carga de datos

La carga oficial es `athena/etl/` (CTAS desde `raw/`; el orden de ejecución está en su README). Escribe los Parquet en `curated/` y `analytics/`, y su último paso de hechos ejecuta `MSCK REPAIR TABLE hechos_compras`, así que el pipeline mantiene sincronizadas las particiones `anio`/`mes` del catálogo.

## Alternativa con crawler

`crawler-config.json` contiene la definición de un crawler que escanea la zona `analytics/` del
bucket y actualiza el catálogo cuando cambian los datos. Es una alternativa a los DDL de Athena y
no forma parte de la carga oficial.

El crawler `crawler-maghsa-compras-analytics` existe en la cuenta (12 targets `analytics/*`, sin schedule y sin ejecuciones).

```bash
aws glue create-crawler --cli-input-json file://crawler-config.json
aws glue start-crawler --name crawler-maghsa-compras-analytics
```

## Sincronizar particiones de hechos_compras

`hechos_compras` está particionada por `anio`/`mes`. Si se agregan objetos a `analytics/hechos_compras/` fuera de `athena/etl/`, hay que sincronizar el catálogo a mano:

```sql
MSCK REPAIR TABLE compras_dwh.hechos_compras;
```
