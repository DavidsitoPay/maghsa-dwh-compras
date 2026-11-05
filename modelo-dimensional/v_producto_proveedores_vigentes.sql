CREATE OR REPLACE VIEW compras_dwh.v_producto_proveedores_vigentes AS
SELECT
    pr.producto_id,
    pr.nombre AS producto,
    pr.categoria_id,
    COUNT(DISTINCT p.proveedor_id) AS proveedores_vigentes
FROM compras_dwh.dim_producto pr
LEFT JOIN compras_dwh.puente_proveedor_producto pxp
    ON pxp.producto_id = pr.producto_id
LEFT JOIN compras_dwh.dim_proveedor p
    ON p.proveedor_id = pxp.proveedor_id
   AND p.estado = 'vigente'
GROUP BY pr.producto_id, pr.nombre, pr.categoria_id;
