"""EjecutorAthena: contexto de start, backoff por throttling, sondeo, timeout y filas."""

import pytest
from athena_ejecutor import ConfigAthena, EjecutorAthena
from conftest import BUCKET, ErrorCliente
from errores import CargaError

TOKEN = "maghsa-carga-20261104120000-00001"
CONFIG = ConfigAthena(workgroup="primary", base="compras_dwh", salida=f"s3://{BUCKET}/athena-results/etl/")


@pytest.fixture
def ejecutor(athena, reloj):
    return EjecutorAthena(athena, reloj, CONFIG)


def test_start_recibe_workgroup_base_salida_y_token(ejecutor, athena):
    ejecutor.ejecutar("SELECT 1 FROM g2_fk", TOKEN, 240)
    inicio = athena.inicios[0]
    assert (inicio["workgroup"], inicio["base"], inicio["salida"], inicio["token"]) == (
        "primary", "compras_dwh", f"s3://{BUCKET}/athena-results/etl/", TOKEN,
    )


def test_token_de_32_caracteres_se_acepta(ejecutor, athena):
    ejecutor.ejecutar("SELECT 1 FROM g2_fk", "t" * 32, 240)
    assert len(athena.inicios) == 1


def test_token_corto_lo_rechaza_athena(ejecutor, athena):
    with pytest.raises(ErrorCliente):
        ejecutor.ejecutar("SELECT 1 FROM g2_fk", "corto", 240)


def test_sondeo_1_1_5_2_25_3_375_5(ejecutor, athena, reloj):
    athena.polls_hasta_final = 5
    ejecutor.ejecutar("SELECT 1 FROM g2_fk", TOKEN, 240)
    assert reloj.dormidos == [1, 1.5, 2.25, 3.375, 5]


def test_throttling_reintenta_con_backoff_y_mismo_token(ejecutor, athena, reloj):
    athena.programar_error("start", "TooManyRequestsException", veces=3)
    ejecutor.ejecutar("SELECT 1 FROM g2_fk", TOKEN, 240)
    assert reloj.dormidos == [1, 2, 4]


def test_throttling_usa_siempre_el_mismo_token(ejecutor, athena):
    athena.programar_error("start", "TooManyRequestsException", veces=3)
    ejecutor.ejecutar("SELECT 1 FROM g2_fk", TOKEN, 240)
    assert set(athena.intentos_inicio) == {TOKEN}


def test_throttling_no_duplica_la_consulta_logica(ejecutor, athena):
    athena.programar_error("start", "TooManyRequestsException", veces=3)
    ejecutor.ejecutar("SELECT 1 FROM g2_fk", TOKEN, 240)
    assert len(athena.inicios) == 1


def test_throttling_agotado_tras_seis_fallos(ejecutor, athena, reloj):
    athena.programar_error("start", "TooManyRequestsException", veces=6)
    with pytest.raises(CargaError) as excinfo:
        ejecutor.ejecutar("SELECT 1 FROM g2_fk", TOKEN, 240)
    assert (excinfo.value.codigo, reloj.dormidos) == ("THROTTLING_AGOTADO", [1, 2, 4, 8, 16])


def test_timeout_detiene_la_consulta(ejecutor, athena):
    athena.colgar("SELECT 1")
    with pytest.raises(CargaError) as excinfo:
        ejecutor.ejecutar("SELECT 1 FROM g2_fk", TOKEN, 240)
    assert (excinfo.value.codigo, athena.detenidas) == (
        "SENTENCIA_TIMEOUT", [athena.inicios[0]["query_id"]],
    )


def test_fallo_de_categoria_sistema_es_reintentable(ejecutor, athena):
    athena.programar_falla("SELECT 1 FROM g2_fk", 1)
    with pytest.raises(CargaError) as excinfo:
        ejecutor.ejecutar("SELECT 1 FROM g2_fk", TOKEN, 240)
    assert excinfo.value.reintentable is True


def test_fallo_de_categoria_usuario_no_es_reintentable(ejecutor, athena):
    athena.programar_falla("SELECT 1 FROM g2_fk", 2)
    with pytest.raises(CargaError) as excinfo:
        ejecutor.ejecutar("SELECT 1 FROM g2_fk", TOKEN, 240)
    assert excinfo.value.reintentable is False


def test_resultado_expone_bytes_escaneados(ejecutor):
    assert ejecutor.ejecutar("SELECT 1 FROM g2_fk", TOKEN, 240).scan_bytes == 1000


def test_filas_incluyen_encabezado_y_nulos(ejecutor, athena):
    athena.programar_compuerta("g2_fk", {"ctrl": "0", "info_filas": None})
    query_id = ejecutor.ejecutar("SELECT 1 FROM g2_fk", TOKEN, 240).query_id
    assert ejecutor.filas(query_id) == [["ctrl", "info_filas"], ["0", None]]
