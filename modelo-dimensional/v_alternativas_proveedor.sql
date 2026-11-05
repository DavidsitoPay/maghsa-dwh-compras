CREATE OR REPLACE VIEW compras_dwh.v_alternativas_proveedor AS
WITH autorizados AS (
    SELECT DISTINCT proveedor_id, producto_id
    FROM compras_dwh.puente_proveedor_producto
),
compras AS (
    SELECT
        proveedor_id,
        producto_id,
        COUNT(DISTINCT id_compra) AS ordenes,
        SUM(cantidad) AS unidades,
        SUM(monto_total) AS gasto,
        SUM(monto_total) / NULLIF(SUM(cantidad), 0) AS precio_promedio,
        AVG(CAST(lead_time_dias AS DOUBLE)) AS lead_time_promedio_dias,
        CAST(date_parse(MAX(fecha_id), '%Y%m%d') AS DATE) AS ultima_compra
    FROM compras_dwh.hechos_compras
    GROUP BY proveedor_id, producto_id
),
base AS (
    SELECT
        a.producto_id,
        pr.nombre AS producto,
        c.nombre_categoria AS categoria,
        a.proveedor_id,
        p.nombre AS proveedor,
        p.estado AS estado_proveedor,
        p.condiciones_pago AS condicion_pago,
        COALESCE(k.ordenes, 0) AS ordenes,
        COALESCE(k.unidades, 0) AS unidades,
        COALESCE(k.gasto, 0) AS gasto,
        k.precio_promedio,
        k.lead_time_promedio_dias,
        k.ultima_compra
    FROM autorizados a
    JOIN compras_dwh.dim_proveedor p ON p.proveedor_id = a.proveedor_id
    JOIN compras_dwh.dim_producto pr ON pr.producto_id = a.producto_id
    LEFT JOIN compras_dwh.dim_categoria c ON c.categoria_id = pr.categoria_id
    LEFT JOIN compras k ON k.proveedor_id = a.proveedor_id AND k.producto_id = a.producto_id
),
ranking AS (
    SELECT
        b.*,
        SUM(gasto) OVER (PARTITION BY producto_id) AS gasto_producto,
        CASE WHEN gasto > 0
             THEN ROW_NUMBER() OVER (PARTITION BY producto_id ORDER BY gasto DESC, ordenes DESC, proveedor_id)
        END AS posicion_gasto
    FROM base b
),
referencia AS (
    SELECT
        r.*,
        MAX(CASE WHEN posicion_gasto = 1 THEN precio_promedio END) OVER (PARTITION BY producto_id) AS precio_principal,
        MAX(CASE WHEN posicion_gasto = 1 THEN lead_time_promedio_dias END) OVER (PARTITION BY producto_id) AS lead_time_principal
    FROM ranking r
)
SELECT
    producto_id,
    producto,
    categoria,
    proveedor,
    estado_proveedor,
    condicion_pago,
    ordenes,
    unidades,
    gasto,
    precio_promedio,
    lead_time_promedio_dias,
    ultima_compra,
    gasto / NULLIF(gasto_producto, 0) AS pct_gasto_producto,
    CASE WHEN gasto_producto = 0 THEN 'sin_compras_producto'
         WHEN posicion_gasto = 1 THEN 'principal'
         WHEN gasto > 0 AND estado_proveedor = 'vigente' THEN 'secundario'
         WHEN gasto > 0 THEN 'secundario_inactivo'
         WHEN estado_proveedor = 'vigente' THEN 'sin_compras_vigente'
         ELSE 'sin_compras_inactivo' END AS situacion_codigo,
    CASE WHEN gasto_producto = 0 THEN 'Producto sin compras (sin principal)'
         WHEN posicion_gasto = 1 AND estado_proveedor = 'vigente' THEN 'Principal (el que más se compró)'
         WHEN posicion_gasto = 1 THEN 'Principal, hoy inactivo'
         WHEN gasto > 0 AND estado_proveedor = 'vigente' THEN 'Alternativa que sí se usó'
         WHEN gasto > 0 THEN 'Inactivo, se le compró antes'
         WHEN estado_proveedor = 'vigente' THEN 'Alternativa nunca usada'
         ELSE 'Inactivo, nunca usado' END AS situacion,
    (precio_promedio - precio_principal) / NULLIF(precio_principal, 0) AS dif_precio_vs_principal_pct,
    lead_time_promedio_dias - lead_time_principal AS dif_lead_time_vs_principal_dias
FROM referencia;
