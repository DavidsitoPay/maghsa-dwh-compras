"""Logs JSON y EMF: la linea EMF es JSON puro con Timestamp entero y Unit por metrica (R5)."""

import json

from conftest import INSTANTE_BASE
from observabilidad import MetricasCorrida, emitir_metricas, registrar


def _emf(capsys) -> dict:
    return json.loads(capsys.readouterr().out.strip())


def _metricas(run_ok: bool = True, rollback_fallido: bool = False) -> MetricasCorrida:
    return MetricasCorrida(
        run_ok=run_ok, duracion_s=12.5, escaneo_gb=0.5, filas_hechos=99, rollback_fallido=rollback_fallido,
    )


def test_emf_timestamp_es_entero_en_milisegundos(capsys):
    emitir_metricas(_metricas(), INSTANTE_BASE)
    assert _emf(capsys)["_aws"]["Timestamp"] == int(INSTANTE_BASE.timestamp() * 1000)


def test_emf_unidades_por_metrica(capsys):
    emitir_metricas(_metricas(), INSTANTE_BASE)
    unidades = {m["Name"]: m["Unit"] for m in _emf(capsys)["_aws"]["CloudWatchMetrics"][0]["Metrics"]}
    assert unidades == {
        "RunOK": "Count",
        "Duracion_s": "Seconds",
        "Escaneo_GB": "Gigabytes",
        "Filas_hechos": "Count",
        "RollbackFallido": "Count",
    }


def test_emf_valores_de_la_corrida(capsys):
    emitir_metricas(_metricas(run_ok=True, rollback_fallido=True), INSTANTE_BASE)
    emf = _emf(capsys)
    assert (emf["RunOK"], emf["Filas_hechos"], emf["RollbackFallido"]) == (1, 99, 1)


def test_emf_dimensiones_vacias_y_namespace(capsys):
    emitir_metricas(_metricas(), INSTANTE_BASE)
    definicion = _emf(capsys)["_aws"]["CloudWatchMetrics"][0]
    assert (definicion["Namespace"], definicion["Dimensions"]) == ("MAGHSA/CargaDWH", [[]])


def test_registrar_emite_una_linea_json(capsys):
    registrar("evento_de_prueba", campo=1)
    assert json.loads(capsys.readouterr().out) == {"evento": "evento_de_prueba", "campo": 1}
