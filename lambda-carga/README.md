# lambda-carga

Carga diaria del DWH de compras de MAGHSA y purga de sus runs. Dos funciones Python 3.12 con `boto3` (`requirements.txt`).

| Función | Handler | Qué hace |
|---|---|---|
| `maghsa-carga-etl` | `runner.lambda_handler` | Ejecuta las sentencias de `athena/etl/` y publica las 12 tablas vivas. |
| `maghsa-purga-runs` | `purga.lambda_handler` | Borra runs antiguos y conserva los 14 más recientes. |

## 1. Carga (`maghsa-carga-etl`)

- Ejecuta las sentencias de `athena/etl/*.sql` (en el zip, bajo `sql/`) en el orden de `orden.txt`. Escribe en `analytics/runs/<run_id>/` y `curated/runs/<run_id>/`. Cada intento usa un `run_id` nuevo (UTC, `yyyyMMddHHmmss`).
- Compuertas: G1 (`07b`), G2.fk, G2.conteo, G2.tiempo y G2.rango (`13`), G3 (`13`, forzable con `forzar_g3`) y G15 (`15`). Una compuerta falla si su fila de control no es cero. Las columnas `info_*` solo se registran.
- Publicación (`14` y después `14p` o `14r` según el modo de `hechos_compras`): repunta las 12 tablas con `ALTER TABLE ... SET LOCATION`. En modo `recreate` recrea `hechos_compras`.
- Si falla después de empezar a publicar, revierte en orden inverso a las ubicaciones guardadas en `previos_<run_id>.json`.
- Reintenta una sola vez, solo ante G2.fk, G2.conteo o un error de sistema de Athena, y solo si quedan al menos 420 s del presupuesto de 840 s.
- Lock en `athena-results/etl/lock.json` con escritura condicional. Si hay una corrida vigente responde `omitida` sin llamar a Athena ni a Glue.
- La verdad de lo publicado es la `Location` de Glue, no los JSON de estado.

## 2. Evento y respuesta

- Evento: `{}` o `{"forzar_g3": true | false}`. Cualquier otra clave o tipo lanza `EVENTO_INVALIDO`.
- Respuesta: `{"estado": "ok" | "omitida", "run_id", "intentos", "duracion_s"}`. Un fallo lanza `CargaError`; su `codigo` aparece en el log `corrida`.
- La purga ignora el evento.

## 3. Estado (`athena-results/etl/`)

- `lock.json`: lock de la carga.
- `ultimo_run.json`: solo se escribe tras G15 correcto.
- `previos_<run_id>.json`: ubicaciones anteriores, escritas antes de cualquier `ALTER`.
- `runs/<run_id>.json`: log de cierre de cada corrida, sea ok o fallo.

## 4. Purga (`maghsa-purga-runs`)

- Conserva los 14 runs más recientes según los `previos_*`.
- No borra nada referenciado por Glue, por `ultimo_run.json` (su `run_id` y su `previo_run_id`) ni por las `location_previa` de los previos de las 14 corridas retenidas.
- Solo considera los prefijos `analytics/runs/<14 dígitos>/` y `curated/runs/<14 dígitos>/`. Nunca toca `managed/`, el legado, `raw/` ni `athena-results/`.
- Siempre registra `purga_plan` antes de borrar. Con `PURGA_MODO=simulacion` no borra. Tope de 5 000 objetos por ejecución, los más antiguos primero, en lotes de 1 000.

## 5. Variables de entorno

| Variable | Función | Valor |
|---|---|---|
| `BUCKET_NAME` | Ambas | Obligatoria. Nombre del bucket del DWH. |
| `GLUE_DATABASE` | Ambas | Por defecto `compras_dwh`. |
| `ATHENA_WORKGROUP` | Carga | Por defecto `primary`. |
| `SQL_DIR` | Carga | Opcional. Por defecto `sql/` junto al código. |
| `PURGA_MODO` | Purga | `simulacion` o `borrar`. |

## 6. Pruebas

Pruebas locales, sin AWS ni boto3. Desde la raíz del repo: `python -m pytest lambda-carga/tests -q` (requiere pytest). Ejecutarlas por separado de `lambda-captura/tests`.

## 7. Paquete

`infra/empaquetar.ps1` arma el zip: los `*.py` en la raíz, `sql/` con `athena/etl/*.sql` y `orden.txt`, y las dependencias de `requirements.txt`. El repo no duplica el SQL.

## 8. Errores y observabilidad

- Códigos de `CargaError`: `EVENTO_INVALIDO`, `LOCK_NO_SOPORTADO`, `WORKGROUP_ENFORCE`, `LOCK_PERDIDO`, `COMPUERTA_FALLIDA`, `SENTENCIA_FALLIDA`, `SENTENCIA_TIMEOUT`, `THROTTLING_AGOTADO`, `PRESUPUESTO_AGOTADO`, `PUBLICACION_FALLIDA`, `UBICACION_PREVIA_INVALIDA`, `PLACEHOLDER_SIN_RESOLVER`, `ORDEN_INVALIDO`, `GATE_INVALIDA`, `SELECT_SIN_MARCA`, `PURGA_MODO_INVALIDO`, `PREVIO_ILEGIBLE`, `CONJUNTO_VIVO_VACIO`, `CLAVE_NO_PERMITIDA` y `BORRADO_PARCIAL`.
- Logs JSON de una línea: `sentencia`, `compuerta`, `corrida`, `purga_plan` y `purga_resultado`.
- Métricas EMF en `MAGHSA/CargaDWH`: `RunOK`, `Duracion_s`, `Escaneo_GB`, `Filas_hechos` y `RollbackFallido`.

## 9. Límites

- La carga necesita escritura condicional `If-Match` en S3, que depende de la versión de boto3 del runtime. Si no está, aborta con `LOCK_NO_SOPORTADO` antes de tocar nada.
- Los hechos cubren hasta 200 meses: `07c` toma los meses de rank 1 a 100 y `07d` los de rank 101 a 200.
- Modo `recreate` (respaldo si falla la proyección): una caída entre el `DROP` y el `CREATE` de `14r` deja `hechos_compras` ausente. La siguiente corrida no converge en ese caso. Recrearla con `14r` (ver `infra/DEPLOY.md`) antes de volver a ejecutar.
- El `run_id` tiene resolución de un segundo. Dos invocaciones que arranquen en el mismo segundo generan el mismo id; el lock impide que corran a la vez (la segunda responde `omitida`) y una corrida dura minutos.
