-- KPI: Gasto, cantidad y precio por producto
-- Precio promedio ponderado, mínimo y máximo: detecta variaciones de precio entre compras

SELECT
    pr.nombre AS producto,
    c.nombre_categoria,
    pr.unidad_medida,
    ROUND(SUM(h.cantidad), 2) AS cantidad_total,
    ROUND(SUM(h.monto_total), 2) AS gasto_total,
    ROUND(SUM(h.monto_total) / NULLIF(SUM(h.cantidad), 0), 2) AS precio_promedio_ponderado,
    ROUND(MIN(h.precio_unitario), 2) AS precio_minimo,
    ROUND(MAX(h.precio_unitario), 2) AS precio_maximo,
    COUNT(DISTINCT h.proveedor_id) AS proveedores_utilizados
FROM compras_dwh.hechos_compras h
JOIN compras_dwh.dim_producto pr
    ON h.producto_id = pr.producto_id
JOIN compras_dwh.dim_categoria c
    ON h.categoria_id = c.categoria_id
GROUP BY pr.nombre, c.nombre_categoria, pr.unidad_medida
ORDER BY gasto_total DESC;
