# Dataset de prueba (sintético)

Datos ficticios generados únicamente para validar el flujo funcional S3 → Glue Data Catalog →
Athena. No corresponden a información real de MAGHSA — sirven solo para probar que la
arquitectura funciona de extremo a extremo con datos de ejemplo pequeños (dentro de la capa
gratuita de AWS).

## Maestros y hechos

| Archivo | Contenido | Corresponde a |
|---|---|---|
| `maestro_proveedores.csv` | 8 proveedores de ejemplo (sin categoría embebida — ver normalización abajo) | `dim_proveedor` |
| `maestro_productos.csv` | 11 productos de ejemplo | `dim_producto` |
| `catalogo_categorias.csv` | 6 categorías de producto de ejemplo | `dim_categoria` |
| `registro_compras.csv` | 97 órdenes de compra de ejemplo (enero–octubre 2026, generadas con `scripts/generar_datos_dummy.py`) (`unidad_organizacional_id`, ya no texto libre) | `hechos_compras` (falta `fecha_id` y `monto_total`, derivables en la carga) |

## Catálogos y relaciones normalizadas (proveedor ↔ categorías ↔ productos)

`categoria_proveedor` dejó de ser una columna de texto libre en `maestro_proveedores.csv`,
porque un proveedor puede pertenecer a más de una categoría (ver `PRV003`, que es tanto
`Repuestos` como `Combustibles`). Se normalizó en las siguientes tablas:

| Archivo | Contenido |
|---|---|
| `categorias_proveedor.csv` | Catálogo de categorías de proveedor (Repuestos, Materia Prima, Servicios, Insumos, Combustibles) |
| `unidades_organizacionales.csv` | Catálogo de unidades organizacionales (antes texto libre en `registro_compras.csv`) |
| `proveedor_categoria_proveedor.csv` | Relación N:M — a qué categoría(s) de proveedor pertenece cada proveedor |
| `categoria_proveedor_x_categoria_producto.csv` | Regla de negocio: qué categorías de producto son válidas para cada categoría de proveedor (usada para filtrar el formulario de ingesta) |
| `proveedor_categoria_producto.csv` | Relación N:M — qué categorías de producto suministra realmente cada proveedor |
| `proveedor_x_producto.csv` | Relación N:M — qué productos específicos suministra cada proveedor (usada para filtrar el dropdown de producto al capturar una compra) |
| `contacto_proveedor.csv` | Datos de contacto por proveedor (nombre, teléfono(s), correo(s) — sin normalizar más, ver nota abajo) |

`contacto_proveedor.csv` no se normalizó a nivel de teléfono/correo individual: cuando un
proveedor tiene más de un número o correo, se separan por coma en la misma celda. Se decidió así
porque, en la práctica, cada contacto suele tener un solo teléfono y un solo correo, y separar
eso en una tabla aparte no aportaría valor proporcional al esfuerzo.

## Siguiente paso para cargar

1. Subir estos CSV a `raw/` en S3 respetando la estructura de `/s3-structure/README.md`.
2. Cargar `curated/` y `analytics/` con las sentencias de `athena/etl/` (orden en `athena/etl/README.md`):
   derivan `fecha_id` y `monto_total` y generan `dim_tiempo` desde la primera fecha de compra hasta hoy.
