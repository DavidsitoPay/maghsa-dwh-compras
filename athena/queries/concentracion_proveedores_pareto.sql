-- KPI: Concentración del gasto en proveedores (análisis de Pareto)
-- Porcentaje individual y acumulado: indica cuántos proveedores concentran el 80% del gasto

WITH gasto AS (
    SELECT
        p.nombre AS proveedor,
        SUM(h.monto_total) AS gasto_total
    FROM compras_dwh.hechos_compras h
    JOIN compras_dwh.dim_proveedor p
        ON h.proveedor_id = p.proveedor_id
    GROUP BY p.nombre
)
SELECT
    proveedor,
    ROUND(gasto_total, 2) AS gasto_total,
    ROUND(100.0 * gasto_total / SUM(gasto_total) OVER (), 2) AS porcentaje_del_total,
    ROUND(100.0 * SUM(gasto_total) OVER (ORDER BY gasto_total DESC)
          / SUM(gasto_total) OVER (), 2) AS porcentaje_acumulado
FROM gasto
ORDER BY gasto_total DESC;
