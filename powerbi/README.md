# Conexión de Power BI con Athena

## Recursos en AWS (us-east-1)

| Recurso | Nombre | Función |
|---|---|---|
| Workgroup de Athena | `maghsa-powerbi` | Aísla las consultas de Power BI; resultados en `s3://maghsa-dwh-compras-070366844944/athena-results/powerbi/`; límite de 10 GB escaneados por consulta |
| Política IAM | `maghsa-powerbi-athena-lectura` | Solo lectura: Athena (workgroup `maghsa-powerbi`), Glue (`compras_dwh`), S3 `analytics/` y escritura únicamente en `athena-results/powerbi/` |
| Usuario IAM | `maghsa-powerbi-athena` | Identidad usada por el conector; tiene adjunta la política anterior |

La clave de acceso del usuario se genera desde la consola de IAM (Seguridad > Crear clave de acceso > "Aplicación fuera de AWS") y no se guarda en el repo.

## Configuración en Windows

1. Instalar el controlador ODBC de Amazon Athena (64 bits).
2. Abrir "Orígenes de datos ODBC (64 bits)" > DSN de sistema > Agregar > Simba Athena ODBC Driver.
3. Configurar el DSN `maghsa-athena`:
   - AWS Region: `us-east-1`
   - Schema: `compras_dwh`
   - Workgroup: `maghsa-powerbi`
   - S3 Output Location: `s3://maghsa-dwh-compras-070366844944/athena-results/powerbi/`
   - Authentication Options: IAM Credentials (clave de acceso y secreto del usuario `maghsa-powerbi-athena`)
4. En Power BI Desktop: Obtener datos > Amazon Athena > DSN `maghsa-athena` > modo **Importar**.
5. Cargar las tablas del modelo estrella y relacionarlas por sus claves (`fecha_id`, `proveedor_id`, `producto_id`, `categoria_id`, `unidad_organizacional_id`).

El modo Importar mantiene el costo bajo: Athena solo consulta en cada actualización, no en cada clic del tablero.

## Modelo semántico

El modelo contiene `hechos_compras`, sus dimensiones (`dim_tiempo`, `dim_proveedor`, `dim_producto`, `dim_categoria`, `dim_unidad_organizacional`) y las vistas ocultas `v_producto_proveedores_vigentes` y `v_alternativas_proveedor`; la segunda tiene una fila por proveedor autorizado y producto con sus compras acumuladas y no se relaciona con las demás tablas, por eso la página Alternativas de proveedor muestra el histórico completo y no responde a los filtros de año y mes. Quedan fuera las tablas puente (`puente_proveedor_categoria_proveedor`, `puente_proveedor_categoria_producto`, `puente_proveedor_producto`), porque relacionarlas con `hechos_compras` duplicaría montos, y las dimensiones `dim_categoria_proveedor` y `dim_contacto_proveedor`, de catálogo y contacto operativo, que no se exponen en el tablero de gerencia. `v_producto_proveedores_vigentes` se relaciona 1:1 con `dim_producto` con filtro bidireccional. El catálogo de proveedores por producto y por categoría se consulta con `athena/queries/proveedores_por_producto.sql` y `proveedores_por_categoria_producto.sql`.

Alternativa disponible = proveedor vigente autorizado distinto del principal (el de mayor gasto acumulado del producto; empate: más órdenes y luego menor código); los inactivos se muestran pero no cuentan; un producto con un solo proveedor autorizado, o sin alternativas vigentes, se lee como dependencia y no como error; un producto sin compras no tiene principal.

## Consultas de soporte (`athena/queries/`)

Cada indicador del dashboard tiene su consulta SQL equivalente, usada para validar las medidas calculadas en Power BI.

| Página del dashboard | Consultas |
|---|---|
| 1. Resumen ejecutivo | `resumen_ejecutivo`, `costo_por_periodo`, `variacion_mensual_gasto`, `variacion_mensual_seguimiento_diario` |
| 2. Gasto y categorías | `gasto_por_categoria`, `gasto_por_unidad_organizacional`, `gasto_por_unidad_y_categoria`, `gasto_y_precio_por_producto` |
| 3. Proveedores | `gasto_por_proveedor`, `concentracion_proveedores_pareto`, `gasto_por_condicion_pago` |
| 4. Desempeño y riesgo | `lead_time_por_proveedor`, `cumplimiento_lead_time`, `riesgo_proveedor_unico` (el KPI se alimenta de la vista `v_producto_proveedores_vigentes`), `compras_a_proveedores_inactivos` |
| 5. Alternativas de proveedor | `alternativas_proveedor_por_producto` |
| Catálogo (consulta puntual) | `proveedores_por_categoria_producto`, `proveedores_por_producto` |

## Variación mensual

El seguimiento compara los días 1..N del mes de la última fecha con datos (`Datos al`) contra el mismo tramo del mes anterior y muestra el % solo si ambos tramos tienen compras suficientes (`Umbral Mínimo Compras`), el mes en curso lleva días suficientes (`Umbral Mínimo Días`) y el gasto previo es mayor que cero; si no, indica el motivo y las compras de cada mes. Los umbrales viven en esas dos medidas y en el CTE `param` de `variacion_mensual_seguimiento_diario`; se cambian y revalidan juntos y son supuestos sin validar con MAGHSA; la cifra oficial compara el mes anterior a ese contra el anterior a él. Las medidas ignoran los segmentadores de año y mes y respetan los demás. `% Productos con Proveedor Único` se calcula sobre la vista `v_producto_proveedores_vigentes` (catálogo completo, único = 1 proveedor vigente) y no reacciona a segmentadores.
