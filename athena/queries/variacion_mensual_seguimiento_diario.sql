-- KPI: Seguimiento diario del gasto, mes en curso (día 1..N) contra el mismo tramo del mes anterior
-- Mes en curso = mes de datos_al (última fecha con compras); N = día de datos_al; % visible desde N >= 5 (supuesto sin validar con MAGHSA)

WITH datos AS (
    SELECT MAX(t.fecha) AS datos_al
    FROM compras_dwh.hechos_compras h
    JOIN compras_dwh.dim_tiempo t ON h.fecha_id = t.fecha_id
),
ancla AS (
    SELECT
        datos_al,
        date_trunc('month', datos_al) AS mes_actual
    FROM datos
),
corte AS (
    SELECT
        datos_al,
        mes_actual,
        date_add('month', -1, mes_actual) AS mes_anterior,
        CASE WHEN datos_al >= mes_actual THEN day(datos_al) ELSE 0 END AS n_dias
    FROM ancla
),
diario AS (
    SELECT
        day(t.fecha) AS dia,
        COALESCE(SUM(h.monto_total) FILTER (WHERE t.fecha >= c.mes_actual), 0) AS gasto_actual,
        COALESCE(SUM(h.monto_total) FILTER (WHERE t.fecha < c.mes_actual), 0) AS gasto_anterior
    FROM corte c
    JOIN compras_dwh.dim_tiempo t
        ON t.fecha >= c.mes_anterior
       AND t.fecha < date_add('month', 1, c.mes_actual)
    LEFT JOIN compras_dwh.hechos_compras h
        ON h.fecha_id = t.fecha_id
    GROUP BY day(t.fecha)
),
acumulado AS (
    SELECT
        d.dia,
        c.mes_actual,
        c.mes_anterior,
        c.datos_al,
        c.n_dias,
        CASE WHEN d.dia <= c.n_dias THEN d.gasto_actual END AS gasto_dia_actual,
        d.gasto_anterior AS gasto_dia_anterior,
        CASE WHEN d.dia <= c.n_dias THEN SUM(d.gasto_actual) OVER (ORDER BY d.dia) END AS gasto_acum_actual,
        SUM(d.gasto_anterior) OVER (ORDER BY d.dia) AS gasto_acum_anterior
    FROM diario d
    CROSS JOIN corte c
),
tramo AS (
    SELECT
        dia, mes_actual, mes_anterior, datos_al, n_dias,
        gasto_dia_actual, gasto_dia_anterior, gasto_acum_actual, gasto_acum_anterior,
        MAX(gasto_acum_actual) OVER () AS gasto_tramo_actual,
        MAX(CASE WHEN dia = n_dias THEN gasto_acum_anterior END) OVER () AS gasto_tramo_anterior
    FROM acumulado
)
SELECT
    dia,
    mes_actual,
    mes_anterior,
    datos_al,
    n_dias,
    ROUND(gasto_dia_actual, 2) AS gasto_dia_actual,
    ROUND(gasto_dia_anterior, 2) AS gasto_dia_anterior,
    ROUND(gasto_acum_actual, 2) AS gasto_acum_actual,
    ROUND(gasto_acum_anterior, 2) AS gasto_acum_anterior,
    ROUND(gasto_tramo_actual, 2) AS gasto_tramo_actual,
    ROUND(gasto_tramo_anterior, 2) AS gasto_tramo_anterior,
    CASE WHEN n_dias >= 5 AND gasto_tramo_anterior > 0
         THEN ROUND(100.0 * (gasto_tramo_actual - gasto_tramo_anterior) / gasto_tramo_anterior, 2)
    END AS variacion_pct
FROM tramo
ORDER BY dia;
