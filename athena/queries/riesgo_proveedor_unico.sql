-- KPI: Productos con proveedor único. Productos que dependen de un único proveedor vigente, sin alternativa de abastecimiento inmediata.
-- KPI de riesgo: productos que dependen de un único proveedor vigente
-- Un producto con un solo proveedor no tiene alternativa de abastecimiento inmediata

SELECT
    pr.producto_id,
    pr.nombre AS producto,
    c.nombre_categoria,
    COUNT(*) AS proveedores_vigentes,
    ARRAY_JOIN(ARRAY_AGG(p.nombre), ', ') AS proveedores
FROM compras_dwh.puente_proveedor_producto pxp
JOIN compras_dwh.dim_proveedor p
    ON pxp.proveedor_id = p.proveedor_id
   AND p.estado = 'vigente'
JOIN compras_dwh.dim_producto pr
    ON pxp.producto_id = pr.producto_id
JOIN compras_dwh.dim_categoria c
    ON pr.categoria_id = c.categoria_id
GROUP BY pr.producto_id, pr.nombre, c.nombre_categoria
HAVING COUNT(*) = 1
ORDER BY pr.nombre;
