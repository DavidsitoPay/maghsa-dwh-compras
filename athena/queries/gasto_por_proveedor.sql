-- KPI: Gasto total por proveedor, ordenado de mayor a menor
-- Útil para identificar concentración de gasto (top proveedores)

SELECT
    p.nombre AS proveedor,
    p.categoria_proveedor,
    COUNT(h.id_compra) AS cantidad_ordenes,
    ROUND(SUM(h.monto_total), 2) AS gasto_total
FROM compras_dwh.hechos_compras h
JOIN compras_dwh.dim_proveedor p
    ON h.proveedor_id = p.proveedor_id
GROUP BY p.nombre, p.categoria_proveedor
ORDER BY gasto_total DESC;
