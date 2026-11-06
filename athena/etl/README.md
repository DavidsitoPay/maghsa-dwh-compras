# Carga a Athena (raw -> curated/analytics)

Proceso de carga oficial del DWH. Cada archivo `.sql` contiene sentencias separadas por `;`; se envían de una en una al workgroup `primary` (base `compras_dwh`). `orden.txt` fija el orden de ejecución, un archivo por línea. La Lambda `maghsa-carga-etl` (`lambda-carga/`) lo ejecuta. Su Schedule diario existe en `DISABLED`: hasta activarlo, la carga corre solo por invocación manual.

Formato de los archivos: las líneas que empiezan por `--` se ignoran; ninguna línea lleva `--` después de código; no hay `;` dentro de literales. Un `SELECT` solo se admite como compuerta, con la marca `-- GATE: <id> ZERO|ZERO_FORZABLE` encima: devuelve una fila con columnas numéricas que deben valer 0 (las `info_*` solo se registran); `ZERO_FORZABLE` admite omitirse con `{"forzar_g3": true}`.

Placeholders: `<bucket-maghsa-dwh>` (bucket de datos), `<run_id>` (`yyyyMMddHHmmss` UTC, nuevo en cada intento) y `<location_hechos>` (solo `14r`). El runner los sustituye antes de enviar; si queda otro `<...>` no se envía nada.

## Flujo

Cada corrida escribe sus tablas en `analytics/runs/<run_id>/<tabla>/` y `curated/runs/<run_id>/<entidad>/` (CTAS con `external_location`), valida y solo entonces repunta las 12 tablas vivas con `ALTER TABLE ... SET LOCATION`. Los datos publicados anteriores quedan intactos hasta su purga. `analytics/<tabla>/` y `curated/<entidad>/` sin `runs/` son el respaldo congelado.

| Paso | Archivo | Qué hace |
|---|---|---|
| 1 | `01`-`06`, `09`-`12` | CTAS por entidad desde `raw/` hacia `tmp_a_*` (analytics) y `tmp_c_*` (curated) |
| 2 | `07a` | Tablas `tmp_csv_compras` (todas las particiones; `MSCK REPAIR`) y `tmp_csv_compras_web`, y vista `tmp_v_compras`; `anio`/`mes` de las web salen de `fecha`; fechas posteriores a hoy (Guatemala) no entran |
| 3 | `07b` | Compuerta `G1`: ids únicos, formato de fecha, partición, importes, lead time y FK contra las `tmp_a_*` |
| 4 | `07c`, `07d` | `tmp_a_hechos` y `tmp_c_compras`, particionadas por `anio`/`mes`: `07c` los primeros 100 meses (CTAS), `07d` los meses 101-200 (INSERT); `lead_time_dias` vacío = NULL |
| 5 | `08` | `tmp_a_tiempo`: `dim_tiempo` de la primera fecha de `tmp_a_hechos` a hoy |
| 6 | `13` | Compuertas `G2.fk`, `G2.conteo`, `G2.tiempo`, `G2.rango` y `G3` (variación de filas 0.8x-4x contra el vivo) |
| 7 | `14` | `SET LOCATION` de 10 tablas y `dim_tiempo` |
| 8 | `14p` o `14r` | `hechos_compras`: `14p` (proyección activa) repunta; `14r` (sin proyección) la recrea sobre `<location_hechos>` y ejecuta `MSCK REPAIR` |
| 9 | `15` | Compuerta `G15`: conteos y monto de las 12 tablas vivas = los de la corrida; si falla, rollback |
| 10 | `99` | Borra `tmp_*` y `tmp_v_compras` (los datos quedan en S3) |

`07c`/`07d` cubren 200 meses; `G2.rango` falla si hay más o si hay años fuera de 2024-2035 (rango de proyección de `hechos_compras`).
Reglas: las compuertas corren antes de publicar; si una falla, no se toca nada vivo. Ninguna sentencia borra datos de S3.
