-- KPI: Matriz de gasto unidad organizacional x categoría (mapa de calor)
-- Muestra en qué categorías gasta cada unidad

SELECT
    u.nombre AS unidad_organizacional,
    c.familia_gasto,
    c.nombre_categoria,
    ROUND(SUM(h.monto_total), 2) AS gasto_total
FROM compras_dwh.hechos_compras h
JOIN compras_dwh.dim_unidad_organizacional u
    ON h.unidad_organizacional_id = u.unidad_organizacional_id
JOIN compras_dwh.dim_categoria c
    ON h.categoria_id = c.categoria_id
GROUP BY u.nombre, c.familia_gasto, c.nombre_categoria
ORDER BY u.nombre, gasto_total DESC;
