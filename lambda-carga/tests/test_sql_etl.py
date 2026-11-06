"""Lectura de athena/etl: divisor de sentencias, marcas GATE, orden.txt y placeholders."""

import pytest
from conftest import ORDEN_SINTETICO
from errores import CargaError
from sql_etl import (
    MarcaGate,
    Sentencia,
    cargar_plantillas,
    clave_archivo,
    dividir_sentencias,
    leer_orden,
    renderizar,
)
from tablas import HECHOS, TABLAS_VIVAS

VALORES = {"bucket": "b", "run_id": "r", "location_hechos": "l"}


def textos(sql: str) -> list[str]:
    return [sentencia.texto for sentencia in dividir_sentencias("x.sql", sql)]


def una_sentencia(sql: str) -> Sentencia:
    return dividir_sentencias("x.sql", sql)[0]


def test_comentario_con_punto_y_coma_y_comilla_se_ignora():
    assert textos("-- nota; it's\nCREATE TABLE t AS SELECT 1;") == ["CREATE TABLE t AS SELECT 1"]


def test_punto_y_coma_dentro_de_literal_no_divide():
    assert textos("CREATE TABLE t AS SELECT 'a;b' AS x;") == ["CREATE TABLE t AS SELECT 'a;b' AS x"]


def test_comilla_escapada_no_cierra_el_literal():
    assert textos("CREATE TABLE t AS SELECT 'it''s' AS y;") == ["CREATE TABLE t AS SELECT 'it''s' AS y"]


def test_sentencias_vacias_se_descartan():
    assert textos(";;\n  ;\nCREATE TABLE t AS SELECT 1;") == ["CREATE TABLE t AS SELECT 1"]


def test_marca_gate_se_asocia_si_solo_hay_comentarios_entre_marca_y_sentencia():
    assert una_sentencia("-- GATE: G1 ZERO\n-- otro\nSELECT 1 FROM x;").marca == MarcaGate(id="G1", forzable=False)


def test_marca_gate_forzable_se_reconoce():
    assert una_sentencia("-- GATE: G3 ZERO_FORZABLE\nSELECT 1 FROM x;").marca == MarcaGate(id="G3", forzable=True)


def test_linea_en_blanco_separa_marca_de_sentencia():
    with pytest.raises(CargaError) as excinfo:
        dividir_sentencias("x.sql", "-- GATE: G1 ZERO\n\nSELECT 1 FROM x;")
    assert excinfo.value.codigo == "SELECT_SIN_MARCA"


@pytest.mark.parametrize("sql", ["SELECT 1;", "WITH a AS (SELECT 1) SELECT * FROM a;", "SHOW TABLES;"])
def test_lectura_sin_marca_es_error(sql):
    with pytest.raises(CargaError) as excinfo:
        dividir_sentencias("x.sql", sql)
    assert excinfo.value.codigo == "SELECT_SIN_MARCA"


def test_marca_con_modo_desconocido_es_error():
    with pytest.raises(CargaError) as excinfo:
        dividir_sentencias("x.sql", "-- GATE: G1 MAYBE\nSELECT 1 FROM x;")
    assert excinfo.value.codigo == "GATE_INVALIDA"


def test_marca_sobre_ddl_es_error():
    with pytest.raises(CargaError) as excinfo:
        dividir_sentencias("x.sql", "-- GATE: G1 ZERO\nCREATE TABLE t AS SELECT 1;")
    assert excinfo.value.codigo == "GATE_INVALIDA"


@pytest.mark.parametrize(
    ("sql", "tipo", "tabla"),
    [
        ("CREATE TABLE tmp_x WITH (external_location='s3://b/x/') AS SELECT 1", "CTAS", "tmp_x"),
        ("INSERT INTO tmp_a_hechos SELECT 1", "INSERT", "tmp_a_hechos"),
        ("ALTER TABLE dim SET LOCATION 's3://b/x/'", "DDL", "dim"),
        ("DROP VIEW IF EXISTS v", "DDL", "v"),
        ("MSCK REPAIR TABLE h", "DDL", "h"),
    ],
)
def test_tipo_y_tabla_de_cada_sentencia(sql, tipo, tabla):
    sentencia = una_sentencia(sql)
    assert (sentencia.tipo, sentencia.tabla) == (tipo, tabla)


def test_renderizar_sustituye_los_tres_placeholders():
    sentencia = Sentencia("x.sql", "SELECT '<bucket-maghsa-dwh>', '<run_id>', '<location_hechos>'", None, "DDL", None)
    assert renderizar(sentencia, VALORES) == "SELECT 'b', 'r', 'l'"


def test_placeholder_sin_resolver_es_error():
    sentencia = Sentencia("x.sql", "SELECT '<foo-bar>'", None, "DDL", None)
    with pytest.raises(CargaError) as excinfo:
        renderizar(sentencia, VALORES)
    assert excinfo.value.codigo == "PLACEHOLDER_SIN_RESOLVER"


def test_comparacion_con_menor_que_no_es_placeholder():
    sentencia = Sentencia("x.sql", "SELECT 1 WHERE a < b and c > d", None, "DDL", None)
    assert renderizar(sentencia, VALORES) == "SELECT 1 WHERE a < b and c > d"


def test_leer_orden_acepta_con_y_sin_sql_y_omite_vacias_y_comentarios(tmp_path):
    (tmp_path / "orden.txt").write_text("01\n# comentario\n\n07a_hechos.sql\n  15  \n99\n", encoding="utf-8")
    assert leer_orden(tmp_path) == ["01", "07a", "15", "99"]


def test_leer_orden_sin_archivo_es_error(tmp_path):
    with pytest.raises(CargaError) as excinfo:
        leer_orden(tmp_path)
    assert excinfo.value.codigo == "ORDEN_INVALIDO"


def test_clave_de_archivo_es_el_prefijo_antes_del_primer_guion_bajo():
    assert clave_archivo("14p_publicar_hechos_P.sql") == "14p"


def test_14_con_tabla_faltante_es_orden_invalido(sql_dir):
    (sql_dir / "14_publicar.sql").write_text(
        "ALTER TABLE dim_proveedor SET LOCATION 's3://b/x/';\n", encoding="utf-8"
    )
    with pytest.raises(CargaError) as excinfo:
        cargar_plantillas(sql_dir)
    assert excinfo.value.codigo == "ORDEN_INVALIDO"


def test_14_con_tabla_repetida_es_orden_invalido(sql_dir):
    vivas = [t for t in TABLAS_VIVAS if t != HECHOS]
    lineas = [f"ALTER TABLE {t} SET LOCATION 's3://b/x/';" for t in vivas]
    lineas[-1] = "ALTER TABLE dim_proveedor SET LOCATION 's3://b/x/';"
    (sql_dir / "14_publicar.sql").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    with pytest.raises(CargaError) as excinfo:
        cargar_plantillas(sql_dir)
    assert excinfo.value.codigo == "ORDEN_INVALIDO"


def test_orden_sintetico_se_carga_completo(sql_dir):
    orden, _ = cargar_plantillas(sql_dir)
    assert orden == ORDEN_SINTETICO
