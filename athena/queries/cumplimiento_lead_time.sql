-- KPI: Cumplimiento de entrega por proveedor
-- Porcentaje de órdenes entregadas dentro del umbral de días (en esta consulta: 7).
-- Ajustar el umbral en la condición 'h.lead_time_dias <= 7' según la política de MAGHSA.

SELECT
    p.nombre AS proveedor,
    COUNT(DISTINCT h.id_compra) AS ordenes_evaluadas,
    ROUND(AVG(h.lead_time_dias), 1) AS lead_time_promedio_dias,
    MAX(h.lead_time_dias) AS lead_time_maximo_dias,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN h.lead_time_dias <= 7 THEN h.id_compra END)
          / COUNT(DISTINCT h.id_compra), 1) AS pct_entregas_en_umbral
FROM compras_dwh.hechos_compras h
JOIN compras_dwh.dim_proveedor p
    ON h.proveedor_id = p.proveedor_id
GROUP BY p.nombre
ORDER BY pct_entregas_en_umbral DESC, lead_time_promedio_dias ASC;
