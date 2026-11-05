-- KPI: Variación mensual del gasto, último mes completo contra el anterior completo (cifra oficial); mes completo = anterior al mes de la última fecha con datos

WITH hoy AS (
    SELECT MAX(t.fecha) AS fecha FROM compras_dwh.hechos_compras h JOIN compras_dwh.dim_tiempo t ON h.fecha_id = t.fecha_id
),
mensual AS (
    SELECT
        t.anio,
        t.mes,
        MAX(t.nombre_mes) AS nombre_mes,
        COALESCE(SUM(h.monto_total), 0) AS gasto
    FROM compras_dwh.dim_tiempo t
    CROSS JOIN hoy
    LEFT JOIN compras_dwh.hechos_compras h
        ON h.fecha_id = t.fecha_id
    WHERE t.fecha < date_trunc('month', hoy.fecha)
    GROUP BY t.anio, t.mes
)
SELECT
    anio,
    mes,
    nombre_mes,
    ROUND(gasto, 2) AS gasto_mes,
    ROUND(LAG(gasto) OVER (ORDER BY anio, mes), 2) AS gasto_mes_anterior,
    ROUND(100.0 * (gasto - LAG(gasto) OVER (ORDER BY anio, mes))
          / NULLIF(LAG(gasto) OVER (ORDER BY anio, mes), 0), 2) AS variacion_pct,
    ROUND(SUM(gasto) OVER (PARTITION BY anio ORDER BY mes), 2) AS gasto_acumulado_anio,
    ROW_NUMBER() OVER (ORDER BY anio DESC, mes DESC) = 1 AS es_ultimo_mes_completo
FROM mensual
ORDER BY anio, mes;
