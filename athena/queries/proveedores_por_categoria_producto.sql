-- Consulta de catálogo (no es un KPI de monto): ¿qué proveedores vigentes
-- suministran una categoría de producto dada? Útil para saber rápido con
-- quién cotizar sin tener que buscar en el historial de compras.
--
-- Reemplazar 'CAT05' por la categoría de interés.

SELECT
    p.proveedor_id,
    p.nombre AS proveedor,
    p.condiciones_pago,
    p.estado,
    c.nombre_categoria
FROM compras_dwh.puente_proveedor_categoria_producto pcp
JOIN compras_dwh.dim_proveedor p
    ON pcp.proveedor_id = p.proveedor_id
JOIN compras_dwh.dim_categoria c
    ON pcp.categoria_id = c.categoria_id
WHERE pcp.categoria_id = 'CAT05'
  AND p.estado = 'vigente'
ORDER BY p.nombre;
