-- KPI: Alternativas de proveedor por producto. Proveedores vigentes autorizados distintos del principal (el de mayor gasto), cuántos se usaron alguna vez y cuántos nunca.
SELECT
    producto,
    categoria,
    COUNT_IF(situacion_codigo IN ('secundario', 'sin_compras_vigente')) AS alternativas_disponibles,
    COUNT_IF(situacion_codigo = 'secundario') AS alternativas_utilizadas,
    COUNT_IF(situacion_codigo = 'sin_compras_vigente') AS alternativas_nunca_utilizadas
FROM compras_dwh.v_alternativas_proveedor
GROUP BY producto, categoria
ORDER BY alternativas_nunca_utilizadas DESC, producto;
