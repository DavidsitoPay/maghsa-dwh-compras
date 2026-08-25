-- KPI: Lead time promedio (días de entrega) por proveedor
-- Apoya la evaluación de desempeño de proveedores (oportunidad de entrega)

SELECT
    p.nombre AS proveedor,
    COUNT(h.id_compra) AS ordenes_evaluadas,
    ROUND(AVG(h.lead_time_dias), 1) AS lead_time_promedio_dias
FROM compras_dwh.hechos_compras h
JOIN compras_dwh.dim_proveedor p
    ON h.proveedor_id = p.proveedor_id
GROUP BY p.nombre
ORDER BY lead_time_promedio_dias ASC;
