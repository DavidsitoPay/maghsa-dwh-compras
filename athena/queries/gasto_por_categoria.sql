-- KPI: Distribución del gasto por categoría / familia de gasto
-- Útil para participación porcentual por categoría

SELECT
    c.nombre_categoria,
    c.familia_gasto,
    ROUND(SUM(h.monto_total), 2) AS gasto_total,
    ROUND(100.0 * SUM(h.monto_total) / SUM(SUM(h.monto_total)) OVER (), 2) AS porcentaje_del_total
FROM compras_dwh.hechos_compras h
JOIN compras_dwh.dim_categoria c
    ON h.categoria_id = c.categoria_id
GROUP BY c.nombre_categoria, c.familia_gasto
ORDER BY gasto_total DESC;
