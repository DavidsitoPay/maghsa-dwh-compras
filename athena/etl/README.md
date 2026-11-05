# Carga a Athena (raw -> curated/analytics)

Proceso de carga oficial del DWH. Cada archivo `.sql` contiene sentencias separadas por `;` que se envían una a una (workgroup `primary`, base `compras_dwh`), ignorando las líneas `--`. Reemplazar `<bucket-maghsa-dwh>` por el bucket real.

Cada entidad se carga con CTAS: lee los CSV de `raw/` mediante tablas temporales `tmp_*` y escribe Parquet SNAPPY en `curated/<destino>/` y `analytics/<destino>/`. Las tablas `tmp_*` se crean y se borran dentro del mismo archivo; la excepción son las de los hechos, que `07a` crea y `07c` borra. Los datos quedan en S3.

## Orden de ejecución

Requisito previo: la base `compras_dwh` y las tablas externas de `modelo-dimensional/` (apuntan a `analytics/`).

| Paso | Archivo | Qué hace | Lee | Tipo |
|---|---|---|---|---|
| 1 | `01`-`06` | Maestros y puentes: `dim_proveedor`, `dim_producto`, `dim_contacto_proveedor`, `puente_proveedor_categoria_proveedor`, `puente_proveedor_categoria_producto`, `puente_proveedor_producto` | `raw/` | CTAS |
| 2 | `09`-`12` | Catálogos: `dim_categoria`, `dim_categoria_proveedor`, `dim_unidad_organizacional`, `categoria_proveedor_x_categoria_producto` | `raw/` | CTAS |
| 3 | `07a_hechos_origen.sql` | Crea las tablas temporales sobre `raw/compras/` (todas las particiones; ejecuta `MSCK REPAIR TABLE tmp_csv_compras`) y `raw/compras_web/`, y la vista `tmp_v_compras` que las une; `anio`/`mes` de las compras web salen de `fecha`; las compras con fecha posterior a hoy no entran | `raw/` | Tablas y vista temporales |
| 4 | `07b_hechos_validacion.sql` | Valida el origen y los vínculos con `dim_proveedor`, `dim_producto`, `dim_categoria` y `dim_unidad_organizacional` | `tmp_v_compras` (paso 3), pasos 1 y 2 | Solo lectura |
| 5 | `07c_hechos_carga.sql` | CTAS de `hechos_compras` y `curated/compras`, particionados por `anio`/`mes`; `lead_time_dias` vacío = NULL; borra las tablas temporales y cierra con `MSCK REPAIR TABLE hechos_compras` | `tmp_v_compras` (paso 3) | CTAS |
| 6 | `08_dim_tiempo.sql` | `dim_tiempo` desde la primera fecha de `hechos_compras` hasta hoy (hora de Guatemala) | `hechos_compras` (paso 5) | CTAS |
| 7 | `13_validacion_posterior.sql` | Conteos, ids duplicados, hechos sin fecha en `dim_tiempo`, rango de `dim_tiempo` | pasos 5 y 6 | Solo lectura |

`07b` necesita las cuatro dimensiones de los pasos 1 y 2 porque hace LEFT JOIN a ellas; `07c` no depende de ninguna dimensión. Ningún paso depende de `10` ni de `12`.

`07b` debe dar: `filas = ids_distintos`; 0 en `fecha_mal_formato`, `particion_inconsistente`, `importe_invalido`, `lead_time_invalido` y en todos los `sin_*`. `lead_time_vacio` se informa pero no bloquea la carga. La última consulta de `07b` lee el `hechos_compras` existente antes de cargar: en la primera carga da `dias = 0`. `13` debe dar `ids_distintos = filas` y `hechos_sin_dim_tiempo = 0`.

## Rango de fechas

Sin años fijos: `raw/compras/` se lee completo y `dim_tiempo` va de la primera compra a hoy y se vuelve a calcular en cada recarga. `MSCK REPAIR TABLE hechos_compras` corre al final de `07c` y registra las particiones nuevas.

## Recarga

Un CTAS con `external_location` exige que el prefijo destino esté vacío (`HIVE_PATH_ALREADY_EXISTS`). Para recargar una entidad hay que borrar antes `analytics/<destino>/` y `curated/<destino>/`.

- El borrado es destructivo y en producción: requiere confirmación del usuario y un respaldo previo.
- Mientras dura la recarga, el dashboard no tiene esos datos.
- Ejecutar `07b` antes del borrado: si no da los resultados esperados, no se borra.
