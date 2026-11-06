DROP TABLE IF EXISTS tmp_a_tiempo;
CREATE TABLE tmp_a_tiempo WITH (format='PARQUET', parquet_compression='SNAPPY', external_location='s3://<bucket-maghsa-dwh>/analytics/runs/<run_id>/dim_tiempo/') AS
SELECT date_format(d,'%Y%m%d') AS fecha_id, CAST(d AS date) AS fecha, year(d) AS anio, quarter(d) AS trimestre, month(d) AS mes,
element_at(ARRAY['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'], month(d)) AS nombre_mes,
day(d) AS dia, element_at(ARRAY['Lunes','Martes','Miercoles','Jueves','Viernes','Sabado','Domingo'], day_of_week(d)) AS dia_semana
FROM (
  SELECT date_add('day', m.k * 1000 + u.k, h.desde) AS d
  FROM (SELECT min(date_parse(fecha_id, '%Y%m%d')) AS desde FROM tmp_a_hechos) h
  CROSS JOIN UNNEST(sequence(0, 99)) AS m(k)
  CROSS JOIN UNNEST(sequence(0, 999)) AS u(k)
  WHERE m.k * 1000 + u.k <= date_diff('day', h.desde, CAST(CAST(current_timestamp AT TIME ZONE 'America/Guatemala' AS date) AS timestamp))
) x;
