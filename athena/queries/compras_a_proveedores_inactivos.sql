-- KPI: Compras a proveedores inactivos (control). Gasto y órdenes registrados a proveedores que no están vigentes; cualquier fila es una alerta.
-- Control: compras registradas a proveedores que no están vigentes
-- Resultado esperado: sin filas. Cualquier fila es una alerta de control interno.

SELECT
    p.proveedor_id,
    p.nombre AS proveedor,
    p.estado,
    COUNT(DISTINCT h.id_compra) AS ordenes_de_compra,
    ROUND(SUM(h.monto_total), 2) AS gasto_total,
    MAX(h.fecha_id) AS ultima_compra_fecha_id
FROM compras_dwh.hechos_compras h
JOIN compras_dwh.dim_proveedor p
    ON h.proveedor_id = p.proveedor_id
WHERE p.estado <> 'vigente'
GROUP BY p.proveedor_id, p.nombre, p.estado
ORDER BY gasto_total DESC;
