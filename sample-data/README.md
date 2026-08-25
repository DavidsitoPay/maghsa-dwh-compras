# Dataset de prueba (sintético)

Datos ficticios generados únicamente para validar el flujo funcional S3 → Glue Data Catalog →
Athena. No corresponden a información real de MAGHSA — sirven solo para probar que la
arquitectura funciona de extremo a extremo con datos de ejemplo pequeños (dentro de la capa
gratuita de AWS).

| Archivo | Contenido | Corresponde a |
|---|---|---|
| `maestro_proveedores.csv` | 6 proveedores de ejemplo | `dim_proveedor` |
| `maestro_productos.csv` | 6 productos de ejemplo | `dim_producto` |
| `catalogo_categorias.csv` | 6 categorías de ejemplo | `dim_categoria` |
| `registro_compras.csv` | 10 órdenes de compra de ejemplo | `hechos_compras` (falta `fecha_id` y `monto_total`, derivables en la carga) |

## Siguiente paso para cargar

1. Subir estos CSV a `raw/` en S3 respetando la estructura de `/s3-structure/README.md`.
2. Convertir a Parquet y calcular columnas derivadas (`fecha_id`, `monto_total = cantidad *
   precio_unitario`) antes de moverlos a `curated/`/`analytics/` — puede hacerse con un script
   simple (pandas) o con un Glue Job, según se decida.
3. Generar `dim_tiempo` para el rango de fechas usado (junio–agosto 2026).
