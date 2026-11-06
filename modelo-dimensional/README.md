# Modelo dimensional

Esquema estrella para el análisis de compras, más las tablas de soporte para la relación
proveedor ↔ categoría de proveedor ↔ categoría de producto ↔ producto.

## Tabla de hechos

- `hechos_compras.sql` — grano de una fila por línea de orden de compra. Particionada por
  `anio`/`mes`.

Proyección de particiones (`anio` 2024-2035, `mes` 01-12): no requiere `MSCK REPAIR TABLE`; la ubicación de las 12 tablas la repunta cada carga (`athena/etl/`), la del DDL es la inicial.

## Dimensiones

- `dim_tiempo.sql`, `dim_proveedor.sql`, `dim_producto.sql`, `dim_categoria.sql`,
  `dim_categoria_proveedor.sql`, `dim_unidad_organizacional.sql`, `dim_contacto_proveedor.sql`
  (esta última es dato operativo de consulta puntual, no se usa para agregaciones)

## Tablas puente (relaciones N:M)

Un proveedor puede pertenecer a más de una categoría de proveedor, y puede suministrar más de
una categoría de producto y más de un producto específico. Estas relaciones no caben en una
columna de `dim_proveedor` sin violar normalización, así que viven en tablas puente aparte:

- `puente_proveedor_categoria_proveedor.sql` — proveedor ↔ categoría(s) de proveedor.
- `puente_proveedor_categoria_producto.sql` — proveedor ↔ categoría(s) de producto que suministra.
- `puente_proveedor_producto.sql` — proveedor ↔ producto(s) específico(s) que suministra. No
  repite `categoria_id`: ese dato ya está en `dim_producto`, y duplicarlo generaría datos
  redundantes que podrían desincronizarse.

**Advertencia al escribir consultas:** unir cualquiera de estas tablas puente directamente
contra `hechos_compras` puede duplicar filas de compra si un proveedor tiene más de una
categoría (fan-out clásico de dimensiones multivaluadas). Úsense solo para búsquedas de
catálogo ("¿qué proveedores venden esta categoría/producto?"), no para agregaciones de monto
sin agrupar explícitamente por proveedor primero.

## Tabla de regla de negocio (no es dimensión)

- `categoria_proveedor_x_categoria_producto.sql` — define qué categorías de producto son
  válidas para cada categoría de proveedor. Se usa para filtrar los checkboxes del formulario
  de ingesta (`lambda-captura/`), no para análisis. Se mantiene en `analytics/` solo por
  trazabilidad.

## Vistas

- `v_producto_proveedores_vigentes.sql` — productos del catálogo con su número de proveedores vigentes; base del KPI "% Productos con Proveedor Único" (no es dimensión ni hecho).
- `v_alternativas_proveedor.sql` — una fila por proveedor autorizado y producto, con estado, condición de pago, compras acumuladas, precio y lead time promedio y su diferencia contra el proveedor principal (el de mayor gasto); base de la página "Alternativas de proveedor" (no es dimensión ni hecho).

## Ampliar o revertir la proyección

Comandos manuales (DDL, no los ejecuta la carga):

```sql
ALTER TABLE hechos_compras SET TBLPROPERTIES ('projection.enabled'='true', 'projection.anio.type'='integer', 'projection.anio.range'='2024,2035', 'projection.mes.type'='integer', 'projection.mes.range'='1,12', 'projection.mes.digits'='2');
ALTER TABLE hechos_compras SET TBLPROPERTIES ('projection.anio.range'='2024,2045');
ALTER TABLE hechos_compras SET TBLPROPERTIES ('projection.enabled'='false');
```

- Primera: migrar una tabla existente a proyección.
- Segunda: ampliar el rango. Hacerlo cuando `max(anio) >= 2033` y actualizar las constantes de `G2.rango` en `athena/etl/13_compuertas_publicacion.sql`.
- Tercera: volver a la tabla con particiones registradas; la carga entonces usa `14r`.
- Si `hechos_compras` no existe (solo modo `recreate`, caída entre `DROP` y `CREATE`), recrearla con `athena/etl/14r_publicar_hechos_R.sql` usando la ubicación de `ultimo_run.json`.
- Fallback `enum` (nota manual; no hay SQL de contrato): `projection.mes.type=enum`, `projection.mes.values=01,02,...,12`.
