-- Consulta de catálogo (no es un KPI de monto): ¿qué proveedores vigentes
-- suministran un producto específico? Nivel de detalle más fino que la
-- consulta por categoría — útil cuando ya se sabe exactamente qué producto
-- se necesita cotizar.
--
-- Reemplazar 'PROD005' por el producto de interés.

SELECT
    p.proveedor_id,
    p.nombre AS proveedor,
    p.condiciones_pago,
    p.estado,
    pr.nombre AS producto,
    cont.nombre_contacto,
    cont.telefonos,
    cont.correos
FROM compras_dwh.puente_proveedor_producto pxp
JOIN compras_dwh.dim_proveedor p
    ON pxp.proveedor_id = p.proveedor_id
JOIN compras_dwh.dim_producto pr
    ON pxp.producto_id = pr.producto_id
LEFT JOIN compras_dwh.dim_contacto_proveedor cont
    ON cont.proveedor_id = p.proveedor_id
WHERE pxp.producto_id = 'PROD005'
  AND p.estado = 'vigente'
ORDER BY p.nombre;
