# Despliegue de la carga diaria del DWH

Pasos para crear en AWS la carga automática: dos Lambdas (`maghsa-carga-etl`, `maghsa-purga-runs`), tres roles, logs de 90 días, el tema SNS `maghsa-dwh-alertas`, cuatro alarmas y dos Schedules de EventBridge creados **apagados**.

- Los placeholders `<account-id>` y `<bucket-maghsa-dwh>` se toman de `docs/CODEMAP.md`. El correo de alertas (`$CORREO`) lo pone el usuario en la sesión; nunca se escribe en archivos.
- La cuenta es única y de producción: toda escritura en AWS es real.
- Nada de esta guía se ejecuta sin el visto bueno indicado en su paso.
- Columna **Quién**: `Usuario` = IAM, Lambda, Scheduler, recurso nuevo o acción fuera del sobre de `revisor-aws`; `Revisor` = clase (i) o (ii) del sobre de `revisor-aws`. M1 (ALTER sobre tabla viva) es `Usuario`: el revisor puede emitir ESCALAR, no asumir APROBADO.
- Orden según el contrato, sección 12.

## Variables y renderizado de plantillas (sin escritura en AWS)

```powershell
$ACC='<account-id>'; $BKT='<bucket-maghsa-dwh>'; $CORREO='<correo-alertas>'   # valores reales: docs/CODEMAP.md; el correo lo pone el usuario
$out = Join-Path $env:TEMP 'maghsa-infra'; New-Item -ItemType Directory -Force $out | Out-Null
Get-ChildItem lambda-carga\infra\*.json | ForEach-Object {
  (Get-Content $_.FullName -Raw).Replace('<account-id>',$ACC).Replace('<bucket-maghsa-dwh>',$BKT) |
    Set-Content (Join-Path $out $_.Name) -Encoding ascii }          # ascii: sin BOM
./lambda-carga/infra/empaquetar.ps1 -Salida $out                    # crea $out\maghsa-carga.zip
tar.exe -tf "$out\maghsa-carga.zip" | Select-String 'runner.py|purga.py|sql/orden.txt|boto3/'   # 4 coincidencias
Set-Location $out    # todos los comandos siguientes usan rutas relativas file://x.json
```

Rollback: borrar `$out`.

## Paso 0 (lectura, `consulta-externa`)

- `aws sts get-caller-identity` (no debe ser root).
- `aws lambda get-account-settings --query AccountLimit.UnreservedConcurrentExecutions`.
- `aws s3api get-bucket-policy --bucket $BKT`: confirmar `DenyInsecureTransport`. Si falta, ESCALAR al usuario: T8 no toca la política del bucket.
- `aws s3api get-bucket-versioning --bucket $BKT`: hoy deshabilitado; debe seguir así.
- `aws athena get-work-group --work-group primary --query WorkGroup.Configuration.EnforceWorkGroupConfiguration`: `false`.
- Línea base de la sección 11 del contrato.

La versión de boto3 del runtime no importa: el zip siempre lleva `boto3>=1.36`.

## Pasos de despliegue

| # | Paso | Comandos | Quién | Rollback |
|---|---|---|---|---|
| 1 | Roles y políticas (contrato §12.1) | bloque 1 | Usuario (IAM) | `aws iam delete-role-policy --role-name R --policy-name P` (políticas inline de los 3 roles); `aws iam delete-role --role-name R` (3 roles) |
| 2 | Logs 90 d, SNS, alarmas con acciones desactivadas | bloque 2 | Usuario (recurso nuevo) | `aws cloudwatch delete-alarms --alarm-names` (4 alarmas); `aws sns delete-topic --topic-arn $TOPIC`; `aws logs delete-log-group --log-group-name /aws/lambda/<f>` |
| 3 | `simulate-principal-policy` | bloque 3 | Lectura | n/a |
| 4 | Crear las 2 Lambdas, reintentos 0 (y concurrencia opcional) | bloque 4 | Usuario (despliegue Lambda) | `aws lambda delete-function --function-name <f>` |
| 5 | M1 y M2 (`hechos_compras` con proyección) | bloque 5 | M1: Usuario (el revisor puede emitir ESCALAR; no asumir APROBADO); M2: lectura | M1 inverso: `ALTER TABLE hechos_compras SET TBLPROPERTIES ('projection.enabled'='false')` |
| 6 | Archivo sintético NUEVO bajo `raw/compras_web/` (opcional, prueba de caída) | `aws s3api put-object --bucket $BKT --key raw/compras_web/<nombre-nuevo>.csv --body <archivo> --if-none-match "*"` (412 si la clave existe; verificar que la CLI soporta `--if-none-match`) | Revisor clase (ii) solo si NO sobrescribe; sobrescribir = Usuario | Borrar el archivo lo hace el usuario |
| 7 | Primera corrida manual | bloque 7 | Usuario (no cabe en el sobre) | Usuario: `SET LOCATION` previo desde `previos_<run_id>.json` (el legado `analytics/<tabla>/` nunca se toca); `hechos_compras`: `projection.enabled=false` |
| 8 | Verificación (sección "Paso 8") y segunda corrida | `aws logs tail /aws/lambda/maghsa-carga-etl --since 30m`; reinvocar bloque 7 | Lectura / Usuario | Usuario: idem paso 7 |
| 9 | Purga en `simulacion`, revisar `purga_plan`, luego `borrar` | bloque 9 | Usuario (configuración Lambda) | Volver a `simulacion` |
| 10 | Crear los 2 Schedules `DISABLED` | bloque 10 | Usuario (programado) | `aws scheduler delete-schedule --name <n>` |
| 11 | Encender | bloque 11 | Usuario | bloque 12 (apagar) |

Último paso, tras el 11: `Remove-Item $out -Recurse -Force` (borra los JSON renderizados con cuenta y bucket reales).

### Bloque 1 (roles)

```powershell
aws iam create-role --role-name maghsa-carga-etl-role --assume-role-policy-document file://trust-lambda.json
aws iam put-role-policy --role-name maghsa-carga-etl-role --policy-name carga-etl-acceso --policy-document file://politica-carga-etl.json
aws iam create-role --role-name maghsa-purga-runs-role --assume-role-policy-document file://trust-lambda.json
aws iam put-role-policy --role-name maghsa-purga-runs-role --policy-name purga-runs-acceso --policy-document file://politica-purga-runs.json
aws iam create-role --role-name maghsa-scheduler-lambda-role --assume-role-policy-document file://trust-scheduler.json
aws iam put-role-policy --role-name maghsa-scheduler-lambda-role --policy-name scheduler-invocar-lambdas --policy-document file://politica-scheduler.json
```

### Bloque 2 (logs, SNS, alarmas)

```powershell
foreach ($f in 'maghsa-carga-etl','maghsa-purga-runs') {
  aws logs create-log-group --log-group-name "/aws/lambda/$f" --region us-east-1
  aws logs put-retention-policy --log-group-name "/aws/lambda/$f" --retention-in-days 90 --region us-east-1 }
$TOPIC = aws sns create-topic --name maghsa-dwh-alertas --region us-east-1 --query TopicArn --output text
aws sns subscribe --topic-arn $TOPIC --protocol email --notification-endpoint $CORREO --region us-east-1   # el usuario confirma desde su correo
foreach ($a in (Get-Content alarmas.json -Raw | ConvertFrom-Json)) {
  $a | ConvertTo-Json -Depth 10 | Set-Content alarma-tmp.json -Encoding ascii
  aws cloudwatch put-metric-alarm --cli-input-json file://alarma-tmp.json --region us-east-1 }
```

### Bloque 3 (simulación de políticas)

La simulación solo evalúa políticas de identidad; no ve la política del bucket ni las SCP. Cualquier línea `FALLA` detiene el despliegue.

```powershell
function Sim($rol,$accion,$res,$esperado,$ctx=$null){
  $arn = switch -Wildcard ($res) {
    'wg:*' {"arn:aws:athena:us-east-1:${ACC}:workgroup/$($res.Substring(3))"}
    'gt:*' {"arn:aws:glue:us-east-1:${ACC}:table/compras_dwh/$($res.Substring(3))"}
    'gd:*' {"arn:aws:glue:us-east-1:${ACC}:database/$($res.Substring(3))"}
    'fn:*' {"arn:aws:lambda:us-east-1:${ACC}:function:$($res.Substring(3))"}
    'rol:*' {"arn:aws:iam::${ACC}:role/$($res.Substring(4))"}
    'bucket' {"arn:aws:s3:::$BKT"}
    default {"arn:aws:s3:::$BKT/$res"} }
  $a = @('iam','simulate-principal-policy','--policy-source-arn',"arn:aws:iam::${ACC}:role/$rol",'--action-names',$accion,'--resource-arns',$arn,'--query','EvaluationResults[0].EvalDecision','--output','text')
  if ($ctx) { $a += @('--context-entries',$ctx) }
  $r = & aws @a
  '{0,-12} {1,-30} {2,-45} {3} (esperado {4})' -f ($(if($r -eq $esperado){'OK'}else{'FALLA'})),$accion,$res,$r,$esperado }
$c='maghsa-carga-etl-role'; $p='maghsa-purga-runs-role'
foreach ($k in 'analytics/runs/x','curated/runs/x','raw/x','athena-results/etl/lock.json') { Sim $c s3:DeleteObject $k implicitDeny }
foreach ($k in 'analytics/runs/x','curated/runs/x','athena-results/etl/lock.json') { Sim $c s3:PutObject $k allowed }
foreach ($k in 'raw/x','analytics/dim_proveedor/x','analytics/managed/x','athena-results/powerbi/x') { Sim $c s3:PutObject $k implicitDeny }
Sim $c s3:GetObject raw/x allowed
Sim $c s3:ListBucket bucket allowed 'ContextKeyName=s3:prefix,ContextKeyValues=raw/compras/,ContextKeyType=string'
Sim $c athena:StartQueryExecution wg:primary allowed
Sim $c athena:StartQueryExecution wg:maghsa-powerbi implicitDeny
Sim $c glue:DeleteTable gt:tmp_x allowed
Sim $c glue:DeleteTable gt:hechos_compras allowed
Sim $c glue:DeleteTable gt:dim_proveedor implicitDeny
Sim $c glue:DeleteDatabase gd:compras_dwh implicitDeny
foreach ($k in 'analytics/runs/x','curated/runs/x') { Sim $p s3:DeleteObject $k allowed }
foreach ($k in 'analytics/dim_proveedor/x','curated/proveedores/x','analytics/managed/x','raw/x','athena-results/etl/ultimo_run.json') { Sim $p s3:DeleteObject $k implicitDeny }
Sim $p s3:PutObject analytics/runs/x implicitDeny; Sim $p s3:PutObject athena-results/etl/x implicitDeny
Sim $p glue:DeleteTable gt:x implicitDeny
Sim $p glue:GetPartitions gt:x allowed
Sim $c s3:ListBucket bucket implicitDeny 'ContextKeyName=s3:prefix,ContextKeyValues=athena-results/powerbi/,ContextKeyType=string'
Sim $p s3:ListBucket bucket allowed 'ContextKeyName=s3:prefix,ContextKeyValues=analytics/runs/,ContextKeyType=string'
Sim $p s3:ListBucket bucket implicitDeny 'ContextKeyName=s3:prefix,ContextKeyValues=raw/,ContextKeyType=string'
Sim $p s3:ListBucket bucket implicitDeny
Sim $c glue:DeletePartition gt:hechos_compras implicitDeny
Sim $c glue:BatchGetPartition gt:hechos_compras allowed
Sim $c glue:CreateTable gt:dim_proveedor implicitDeny
foreach ($r in $c,$p) {
  foreach ($a in 'iam:PassRole','sts:AssumeRole','iam:PutRolePolicy') { Sim $r $a 'rol:maghsa-carga-etl-role' implicitDeny }
  Sim $r lambda:UpdateFunctionCode 'fn:maghsa-carga-etl' implicitDeny
  Sim $r s3:PutBucketPolicy bucket implicitDeny }
$s='maghsa-scheduler-lambda-role'
Sim $s lambda:InvokeFunction 'fn:maghsa-carga-etl' allowed
Sim $s lambda:InvokeFunction 'fn:maghsa-purga-runs' allowed
Sim $s lambda:InvokeFunction 'fn:maghsa-captura' implicitDeny
Sim $s lambda:UpdateFunctionCode 'fn:maghsa-carga-etl' implicitDeny
```

Resultado esperado (tabla del contrato §7, con `glue:DeleteTable` acotado a `tmp_*` y `hechos_compras`):

| Principal | Acción / recurso | Esperado |
| --- | --- | --- |
| carga | `s3:DeleteObject` en `analytics/runs/x`, `curated/runs/x`, `raw/x`, `athena-results/etl/lock.json` | implicitDeny (4) |
| carga | `s3:PutObject` en `analytics/runs/x`, `curated/runs/x`, `athena-results/etl/lock.json` | allowed (3) |
| carga | `s3:PutObject` en `raw/x`, `analytics/dim_proveedor/x`, `analytics/managed/x`, `athena-results/powerbi/x` | implicitDeny (4) |
| carga | `s3:GetObject` en `raw/x`; `s3:ListBucket` con `s3:prefix=raw/compras/` | allowed |
| carga | `athena:StartQueryExecution` en `workgroup/primary` / en `workgroup/maghsa-powerbi` | allowed / implicitDeny |
| carga | `glue:DeleteTable` en `table/compras_dwh/tmp_x` y `table/compras_dwh/hechos_compras` / en `table/compras_dwh/dim_proveedor` | allowed (2) / implicitDeny |
| carga | `glue:DeleteDatabase` en `database/compras_dwh` | implicitDeny |
| purga | `s3:DeleteObject` en `analytics/runs/x`, `curated/runs/x` | allowed (2) |
| purga | `s3:DeleteObject` en `analytics/dim_proveedor/x`, `curated/proveedores/x`, `analytics/managed/x`, `raw/x`, `athena-results/etl/ultimo_run.json` | implicitDeny (5) |
| purga | `s3:PutObject` en cualquier prefijo; `glue:DeleteTable`; `glue:GetPartitions` en `table/compras_dwh/x` | implicitDeny, implicitDeny, allowed |
| carga | `s3:ListBucket` con `s3:prefix=athena-results/powerbi/` | implicitDeny |
| carga | `glue:DeletePartition` en `hechos_compras`; `glue:BatchGetPartition` en `hechos_compras`; `glue:CreateTable` en `dim_proveedor` | implicitDeny, allowed, implicitDeny |
| purga | `s3:ListBucket` con `s3:prefix=analytics/runs/` / con `raw/` / sin prefijo | allowed / implicitDeny / implicitDeny |
| carga y purga | `iam:PassRole`, `sts:AssumeRole`, `iam:PutRolePolicy`, `lambda:UpdateFunctionCode` (sobre `maghsa-carga-etl`), `s3:PutBucketPolicy` | implicitDeny (todas) |
| scheduler | `lambda:InvokeFunction` en `maghsa-carga-etl` y `maghsa-purga-runs` / en `maghsa-captura`; `lambda:UpdateFunctionCode` | allowed (2) / implicitDeny (2) |

### Bloque 4 (funciones)

```powershell
$ROL="arn:aws:iam::${ACC}:role/"
aws lambda create-function --function-name maghsa-carga-etl --runtime python3.12 --handler runner.lambda_handler --role "${ROL}maghsa-carga-etl-role" --zip-file fileb://maghsa-carga.zip --timeout 900 --memory-size 256 --environment "Variables={BUCKET_NAME=$BKT,GLUE_DATABASE=compras_dwh,ATHENA_WORKGROUP=primary}" --region us-east-1
aws lambda create-function --function-name maghsa-purga-runs --runtime python3.12 --handler purga.lambda_handler --role "${ROL}maghsa-purga-runs-role" --zip-file fileb://maghsa-carga.zip --timeout 300 --memory-size 256 --environment "Variables={BUCKET_NAME=$BKT,GLUE_DATABASE=compras_dwh,PURGA_MODO=simulacion}" --region us-east-1
foreach ($f in 'maghsa-carga-etl','maghsa-purga-runs') {
  aws lambda wait function-active-v2 --function-name $f --region us-east-1
  aws lambda put-function-event-invoke-config --function-name $f --maximum-retry-attempts 0 --maximum-event-age-in-seconds 60 --region us-east-1 }
# Opcional, solo si el paso 0 dio >= 101:
# aws lambda put-function-concurrency --function-name maghsa-carga-etl --reserved-concurrent-executions 1 --region us-east-1
```

Si `create-function` falla con "role cannot be assumed", esperar unos 10 s (propagación IAM) y repetir. Para redesplegar código: `aws lambda update-function-code --function-name <f> --zip-file fileb://maghsa-carga.zip`. Las funciones nuevas no tienen Function URL: no tienen entrada pública.

### Bloque 5 (migración de `hechos_compras`)

Athena como usuario del autor; workgroup `primary` sin salida fija. M1 lo ejecuta el usuario: es ALTER sobre tabla viva; el revisor puede emitir ESCALAR, no asumir APROBADO.

```powershell
$RC="OutputLocation=s3://$BKT/athena-results/etl/"
$M1 = "ALTER TABLE hechos_compras SET TBLPROPERTIES ('projection.enabled'='true','projection.anio.type'='integer','projection.anio.range'='2024,2035','projection.mes.type'='integer','projection.mes.range'='1,12','projection.mes.digits'='2')"
$q = aws athena start-query-execution --work-group primary --query-execution-context Database=compras_dwh --result-configuration $RC --query-string $M1 --query QueryExecutionId --output text
aws athena get-query-execution --query-execution-id $q --query QueryExecution.Status.State --output text   # SUCCEEDED
```

M2: misma forma con `SELECT anio, mes, count(*) FROM hechos_compras GROUP BY 1,2 ORDER BY 1,2` y `aws athena get-query-results`. Resultado esperado: 10 meses, total 97 (01:8 02:8 03:9 04:9 05:10 06:10 07:10 08:12 09:10 10:11). Si falla: contrato §4 (reintento con `projection.mes.type=enum` y `projection.mes.values=01,...,12`; si también falla, `projection.enabled=false`).

### Bloque 7 (primera corrida)

La CLI reintenta `invoke` tras un timeout de lectura, por eso el timeout es alto; si se duplicara, el lock responde `omitida`.

```powershell
Set-Content evento.json '{}' -Encoding ascii
aws lambda invoke --function-name maghsa-carga-etl --invocation-type RequestResponse --payload fileb://evento.json --cli-read-timeout 920 --cli-connect-timeout 60 --region us-east-1 respuesta.json
Get-Content respuesta.json     # {"estado":"ok","run_id":...}; error = excepcion
```

`{"forzar_g3": true}` solo manual: `Set-Content evento.json '{"forzar_g3":true}'` (en archivo para evitar el escapado de comillas de PowerShell 5.1).

### Bloque 9 (purga)

```powershell
aws lambda invoke --function-name maghsa-purga-runs --payload fileb://evento.json --cli-read-timeout 320 --region us-east-1 respuesta-purga.json
# revisar el log purga_plan con consulta-externa; luego, con el visto bueno del usuario (update reemplaza TODO el mapa de variables):
aws lambda update-function-configuration --function-name maghsa-purga-runs --environment "Variables={BUCKET_NAME=$BKT,GLUE_DATABASE=compras_dwh,PURGA_MODO=borrar}" --region us-east-1
```

### Bloque 10 (Schedules apagados)

```powershell
aws scheduler create-schedule --cli-input-json file://schedule-carga-diaria.json --region us-east-1
aws scheduler create-schedule --cli-input-json file://schedule-purga-semanal.json --region us-east-1
aws scheduler get-schedule --name maghsa-carga-diaria --region us-east-1 --query "[State,ScheduleExpression,ScheduleExpressionTimezone]"   # DISABLED
```

### Bloque 11 (encender)

Mismo JSON con `State` cambiado, nada más. `update-schedule` reemplaza la definición completa: no vale pasar solo `--state`.

```powershell
foreach ($n in 'schedule-carga-diaria','schedule-purga-semanal') {
  $j = Get-Content "$n.json" -Raw | ConvertFrom-Json; $j.State = 'ENABLED'
  $j | ConvertTo-Json -Depth 10 | Set-Content "$n-on.json" -Encoding ascii
  aws scheduler update-schedule --cli-input-json file://$n-on.json --region us-east-1 }
aws cloudwatch enable-alarm-actions --alarm-names maghsa-carga-errores maghsa-carga-duracion maghsa-carga-sin-corrida maghsa-purga-errores --region us-east-1
```

Encender solo tras una corrida manual exitosa en las últimas 26 h; si no, `maghsa-carga-sin-corrida` ya está en ALARM por `breaching`. El mismo día: Schedule y alarmas. Precondición: el archivo sintético inválido del paso 6 fue retirado por el usuario y la última corrida manual es `ok`.

### Bloque 12 (apagar; devuelve el estado inicial)

```powershell
foreach ($n in 'schedule-carga-diaria','schedule-purga-semanal') {
  $j = Get-Content "$n.json" -Raw | ConvertFrom-Json; $j.State = 'DISABLED'
  $j | ConvertTo-Json -Depth 10 | Set-Content "$n-off.json" -Encoding ascii
  aws scheduler update-schedule --cli-input-json file://$n-off.json --region us-east-1 }
aws cloudwatch disable-alarm-actions --alarm-names maghsa-carga-errores maghsa-carga-duracion maghsa-carga-sin-corrida maghsa-purga-errores --region us-east-1
```

Un Schedule `DISABLED` no invoca: costo 0.

## Recuperación: `hechos_compras` ausente (solo recreate)

Si la tabla viva `hechos_compras` falta tras un modo `recreate` interrumpido entre el `DROP` y el `CREATE`, la siguiente corrida no converge por sí sola. El usuario ejecuta a mano las 3 sentencias de `14r` con `LOCATION` = `tablas.hechos_compras` de `ultimo_run.json`. No hay automatismo.

## Paso 8: verificación (`consulta-externa` salvo lo indicado)

1. Paso 0: `DenyInsecureTransport`, versionado deshabilitado, workgroup `primary` sin enforce.
2. M1/M2: proyección (`mes` integer/digits sobre STRING): 10 meses, total 97; si falla, enum y luego `enabled=false`.
3. Simulación IAM con la tabla ajustada (`glue:DeleteTable` acotado); cualquier FALLA detiene.
4. Primera invocación manual: (a) `lock.json` ausente se crea (IAM-1); (b) CTAS/INSERT sin `AccessDenied` (DeleteObject, multipart, Glue); (c) `INSERT INTO ... 0 filas` (07d) termina en `SUCCEEDED`; si no, fallback: G1 emite `info_meses` y el runner omite 07d con <=100 meses; (d) columnas de cada compuerta en el log (`info_filas_nuevo` presente); (e) `duracion_s` vs alarma de 480 s (primer sondeo a 1 s); (f) métrica `MAGHSA/CargaDWH` visible y `Timestamp` aceptado; (g) `ultimo_run.json`/`previos_<id>.json` con 12 claves; (h) `SHOW CREATE TABLE`/Glue: `Location` de las 12 = `runs/<id>/...`; `projection.enabled=true`; (i) `hechos_compras` 97 filas y `sum(monto_total)` igual a la línea base.
5. Corrida doble: conteos iguales, run_ids distintos, lock vigente -> `omitida`.
6. Caída simulada: archivo sintético NUEVO bajo `raw/compras_web/` con fecha válida y `cantidad` no numérica -> G1 corta, `ultimo_run.json` intacto, lock libre.
7. Purga en `simulacion`: revisar `purga_plan` (protegidos incluye el run vigente y los `location_previa`); luego `borrar`.
8. Alarmas en estado esperado antes de habilitar el Scheduler (acciones desactivadas).
