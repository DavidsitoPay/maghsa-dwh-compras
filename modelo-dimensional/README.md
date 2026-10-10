# Modelo dimensional

Esquema estrella para el análisis de compras, más las tablas de soporte para la relación
proveedor ↔ categoría de proveedor ↔ categoría de producto ↔ producto.

## Tabla de hechos

- `hechos_compras.sql` — grano de una fila por línea de orden de compra. Particionada por
  `anio`/`mes`.

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
