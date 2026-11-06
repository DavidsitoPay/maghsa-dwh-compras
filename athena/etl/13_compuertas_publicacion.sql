-- GATE: G2.fk ZERO
SELECT count_if(p.proveedor_id IS NULL) AS sin_proveedor, count_if(pr.producto_id IS NULL) AS sin_producto, count_if(c.categoria_id IS NULL) AS sin_categoria, count_if(u.unidad_organizacional_id IS NULL) AS sin_unidad FROM tmp_a_hechos h LEFT JOIN tmp_a_proveedores p ON h.proveedor_id = p.proveedor_id LEFT JOIN tmp_a_productos pr ON h.producto_id = pr.producto_id LEFT JOIN tmp_a_categorias c ON h.categoria_id = c.categoria_id LEFT JOIN tmp_a_unidades_organizacionales u ON h.unidad_organizacional_id = u.unidad_organizacional_id;
-- GATE: G2.conteo ZERO
SELECT (SELECT count(*) FROM tmp_a_hechos) - (SELECT count(*) FROM tmp_v_compras) AS dif_hechos_vs_origen, (SELECT count(*) FROM tmp_c_compras) - (SELECT count(*) FROM tmp_a_hechos) AS dif_curated_vs_hechos, (SELECT count(*) FROM tmp_a_hechos) - (SELECT count(DISTINCT id_compra) FROM tmp_a_hechos) AS ids_duplicados;
-- GATE: G2.tiempo ZERO
SELECT count(*) AS hechos_sin_dim_tiempo FROM tmp_a_hechos h LEFT JOIN tmp_a_tiempo t ON h.fecha_id = t.fecha_id WHERE t.fecha_id IS NULL;
-- GATE: G2.rango ZERO
SELECT CASE WHEN min(CAST(anio AS integer)) < 2024 THEN 1 ELSE 0 END AS anio_bajo_rango, CASE WHEN max(CAST(anio AS integer)) > 2035 THEN 1 ELSE 0 END AS anio_sobre_rango, CASE WHEN count(DISTINCT concat(anio, mes)) > 200 THEN 1 ELSE 0 END AS meses_sobre_200 FROM tmp_a_hechos;
-- GATE: G3 ZERO_FORZABLE
SELECT CASE WHEN v.n_vivo = 0 THEN 0 WHEN n.n_nuevo < 0.8 * v.n_vivo OR n.n_nuevo > 4 * v.n_vivo THEN 1 ELSE 0 END AS variacion_filas, n.n_nuevo AS info_filas_nuevo, v.n_vivo AS info_filas_vivo FROM (SELECT count(*) AS n_nuevo FROM tmp_a_hechos) n CROSS JOIN (SELECT count(*) AS n_vivo FROM hechos_compras) v;
