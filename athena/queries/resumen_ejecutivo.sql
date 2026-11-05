-- KPI: Resumen ejecutivo de compras (tarjetas del encabezado del dashboard)
-- Gasto total, volumen de órdenes, ticket promedio, proveedores activos y lead time global

SELECT
    ROUND(SUM(h.monto_total), 2) AS gasto_total,
    COUNT(DISTINCT h.id_compra) AS ordenes_de_compra,
    COUNT(*) AS lineas_de_compra,
    ROUND(SUM(h.monto_total) / COUNT(DISTINCT h.id_compra), 2) AS ticket_promedio_por_orden,
    COUNT(DISTINCT h.proveedor_id) AS proveedores_con_compras,
    ROUND(AVG(h.lead_time_dias), 1) AS lead_time_promedio_dias
FROM compras_dwh.hechos_compras h;
