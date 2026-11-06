"""Contrato entre athena/etl/ (SQL real) y el runner: orden, marcas GATE, placeholders y publicacion."""

import re
from pathlib import Path

import pytest
from sql_etl import cargar_plantillas, clave_archivo, leer_orden
from tablas import ETAPA_DE, HECHOS, TABLAS_VIVAS, TMP_CURATED

ETL = Path(__file__).resolve().parents[2] / "athena" / "etl"
GATES_PERMITIDOS = {"G1", "G2.fk", "G2.conteo", "G2.tiempo", "G2.rango", "G3", "G15"}
CLAVES_PUBLICACION = {"14p", "14r"}


@pytest.fixture(scope="module")
def plantillas():
    return cargar_plantillas(ETL)[1]


@pytest.fixture(scope="module")
def sentencias(plantillas):
    return [(clave, sentencia) for clave, lista in plantillas.items() for sentencia in lista]


def texto_de(plantillas, clave: str) -> str:
    return "\n".join(s.texto for s in plantillas[clave])


def test_orden_txt_lista_los_sql_salvo_14p_y_14r():
    archivos = {clave_archivo(ruta.name) for ruta in ETL.glob("*.sql")}
    assert set(leer_orden(ETL)) == archivos - CLAVES_PUBLICACION


def test_cargar_plantillas_del_sql_real_no_falla():
    orden, _ = cargar_plantillas(ETL)
    assert orden[-2:] == ["15", "99"]


def test_location_hechos_solo_aparece_en_14r(sentencias):
    apariciones = {clave for clave, s in sentencias if "<location_hechos>" in s.texto}
    assert apariciones == {"14r"}


def test_marcas_gate_usan_ids_permitidos(sentencias):
    ids = {s.marca.id for _, s in sentencias if s.marca is not None}
    assert ids <= GATES_PERMITIDOS


def test_solo_g3_es_forzable(sentencias):
    forzables = {s.marca.id for _, s in sentencias if s.marca is not None and s.marca.forzable}
    assert forzables == {"G3"}


def test_g15_solo_aparece_en_la_etapa_15(sentencias):
    claves = {clave for clave, s in sentencias if s.marca is not None and s.marca.id == "G15"}
    assert claves == {"15"}


def test_g1_emite_info_filas(plantillas):
    assert "info_filas" in texto_de(plantillas, "07b")


def test_g3_emite_info_filas_nuevo(plantillas):
    assert "info_filas_nuevo" in texto_de(plantillas, "13")


def test_sin_comentario_de_guion_doble_tras_codigo():
    infractores = [
        f"{ruta.name}:{numero}"
        for ruta in ETL.glob("*.sql")
        for numero, linea in enumerate(ruta.read_text(encoding="utf-8").splitlines(), 1)
        if not linea.strip().startswith("--") and "--" in linea
    ]
    assert infractores == []


def test_14_cubre_las_11_tablas_sin_hechos(plantillas):
    tablas = {s.tabla for s in plantillas["14"]}
    assert tablas == set(TABLAS_VIVAS) - {HECHOS}


def test_14_apunta_a_la_ruta_del_run_de_cada_tabla(plantillas):
    fuera = [s.tabla for s in plantillas["14"] if f"runs/<run_id>/{s.tabla}/" not in s.texto]
    assert fuera == []


def test_14p_publica_solo_hechos_por_proyeccion(plantillas):
    assert [s.tabla for s in plantillas["14p"]] == [HECHOS]


def test_14r_recrea_hechos(plantillas):
    texto = texto_de(plantillas, "14r")
    assert ("DROP TABLE IF EXISTS hechos_compras" in texto, "CREATE EXTERNAL TABLE hechos_compras" in texto) == (
        True, True,
    )


def test_15_compara_cada_tabla_viva_con_su_etapa(plantillas):
    texto = texto_de(plantillas, "15")
    faltan = [tabla for tabla in TABLAS_VIVAS if ETAPA_DE[tabla] not in texto]
    assert faltan == []


def test_99_borra_etapa_curated_csv_y_vista(plantillas):
    texto = texto_de(plantillas, "99")
    esperados = set(ETAPA_DE.values()) | set(TMP_CURATED) | {"tmp_v_compras"}
    faltan = [nombre for nombre in esperados if nombre not in texto]
    assert faltan == []


def test_todo_ctas_declara_external_location_bajo_runs(sentencias):
    sin_ubicacion = [
        clave for clave, s in sentencias
        if s.tipo == "CTAS" and not re.search(r"external_location\s*=\s*'s3://<bucket-maghsa-dwh>/[^']*runs/<run_id>/", s.texto)
    ]
    assert sin_ubicacion == []
