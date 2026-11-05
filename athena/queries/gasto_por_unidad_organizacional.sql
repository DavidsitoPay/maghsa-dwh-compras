-- KPI: Gasto por unidad organizacional (quién consume el presupuesto de compras)
-- Responde a la comparación por unidades organizacionales definida en el alcance

SELECT
    u.nombre AS unidad_organizacional,
    COUNT(DISTINCT h.id_compra) AS ordenes_de_compra,
    ROUND(SUM(h.monto_total), 2) AS gasto_total,
    ROUND(100.0 * SUM(h.monto_total) / SUM(SUM(h.monto_total)) OVER (), 2) AS porcentaje_del_total
FROM compras_dwh.hechos_compras h
JOIN compras_dwh.dim_unidad_organizacional u
    ON h.unidad_organizacional_id = u.unidad_organizacional_id
GROUP BY u.nombre
ORDER BY gasto_total DESC;
