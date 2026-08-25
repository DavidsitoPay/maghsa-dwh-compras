-- KPI: Costo total de compras por periodo (año/mes)
-- Permite ver evolución histórica del gasto

SELECT
    t.anio,
    t.mes,
    t.nombre_mes,
    ROUND(SUM(h.monto_total), 2) AS costo_total
FROM compras_dwh.hechos_compras h
JOIN compras_dwh.dim_tiempo t
    ON h.fecha_id = t.fecha_id
GROUP BY t.anio, t.mes, t.nombre_mes
ORDER BY t.anio, t.mes;
