-- KPI: Gasto por condición de pago (contado, 30, 45, 60 días)
-- Apoya la planeación de flujo de caja y la negociación de plazos con proveedores

SELECT
    h.condicion_pago,
    COUNT(DISTINCT h.id_compra) AS ordenes_de_compra,
    ROUND(SUM(h.monto_total), 2) AS gasto_total,
    ROUND(100.0 * SUM(h.monto_total) / SUM(SUM(h.monto_total)) OVER (), 2) AS porcentaje_del_total,
    ROUND(AVG(h.lead_time_dias), 1) AS lead_time_promedio_dias
FROM compras_dwh.hechos_compras h
GROUP BY h.condicion_pago
ORDER BY gasto_total DESC;
