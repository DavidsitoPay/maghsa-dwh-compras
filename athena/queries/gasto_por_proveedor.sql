-- KPI: Gasto total por proveedor, ordenado de mayor a menor
-- Útil para identificar concentración de gasto (top proveedores)
--
-- Nota: categoria_proveedor ya no vive en dim_proveedor (un proveedor puede
-- tener más de una). Las categorías se agregan en una subconsulta ANTES de
-- unir con hechos_compras, para no duplicar filas de compra al unir una
-- relación N:M directamente contra la tabla de hechos (fan-out).

SELECT
    p.nombre AS proveedor,
    cp.categorias_proveedor,
    COUNT(h.id_compra) AS cantidad_ordenes,
    ROUND(SUM(h.monto_total), 2) AS gasto_total
FROM compras_dwh.hechos_compras h
JOIN compras_dwh.dim_proveedor p
    ON h.proveedor_id = p.proveedor_id
LEFT JOIN (
    SELECT
        pcp.proveedor_id,
        ARRAY_JOIN(ARRAY_AGG(dcp.nombre), ', ') AS categorias_proveedor
    FROM compras_dwh.puente_proveedor_categoria_proveedor pcp
    JOIN compras_dwh.dim_categoria_proveedor dcp
        ON pcp.categoria_proveedor_id = dcp.categoria_proveedor_id
    GROUP BY pcp.proveedor_id
) cp
    ON cp.proveedor_id = p.proveedor_id
GROUP BY p.nombre, cp.categorias_proveedor
ORDER BY gasto_total DESC;
