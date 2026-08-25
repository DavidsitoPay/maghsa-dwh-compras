# AWS Glue Data Catalog

Para la evidencia funcional inicial, la forma más rápida es crear la base de datos y correr los
DDL de `/modelo-dimensional/` directamente desde el editor de consultas de Athena — Athena
registra esas tablas en el Glue Data Catalog automáticamente, sin necesidad de esperar un
crawler.

```sql
CREATE DATABASE IF NOT EXISTS compras_dwh;
```

Luego ejecutar en orden los `.sql` de `/modelo-dimensional/`.

## Alternativa con crawler

`crawler-config.json` contiene la definición de un crawler que escanea la zona `analytics/` del
bucket y actualiza el catálogo automáticamente cuando cambian los datos. Útil para la operación
continua, pero no es indispensable para la primera evidencia funcional.

```bash
aws glue create-crawler --cli-input-json file://crawler-config.json
aws glue start-crawler --name crawler-maghsa-compras-analytics
```

## Sincronizar particiones de hechos_compras

Como `hechos_compras` está particionada por `anio`/`mes`, después de cargar datos nuevos hay que
sincronizar el catálogo con las particiones reales en S3:

```sql
MSCK REPAIR TABLE compras_dwh.hechos_compras;
```
