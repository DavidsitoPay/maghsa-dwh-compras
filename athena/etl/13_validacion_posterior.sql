SELECT count(*) AS filas, count(DISTINCT id_compra) AS ids_distintos, count_if(lead_time_dias IS NULL) AS lead_time_nulo, min(fecha_id) AS primera, max(fecha_id) AS ultima FROM hechos_compras;
SELECT anio, mes, count(*) AS compras FROM hechos_compras GROUP BY anio, mes ORDER BY anio, mes;
SELECT count(*) AS hechos_sin_dim_tiempo FROM hechos_compras h LEFT JOIN dim_tiempo t ON h.fecha_id = t.fecha_id WHERE t.fecha_id IS NULL;
SELECT count(*) AS dias, min(fecha) AS desde, max(fecha) AS hasta FROM dim_tiempo;
