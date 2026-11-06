"""Evaluacion de compuertas: una fila de datos y columnas de control en cero."""

import pytest
from compuertas import evaluar


@pytest.mark.parametrize(
    ("filas", "esperado"),
    [
        ([["ctrl"]], False),
        ([["ctrl"], ["0"], ["0"]], False),
        ([], False),
        ([["ctrl"], [None]], False),
        ([["ctrl"], ["abc"]], False),
        ([["ctrl"], ["1"]], False),
        ([["ctrl"], ["0"]], True),
        ([["ctrl"], ["0.00"]], True),
        ([["ctrl", "info_x"], ["0", "5"]], True),
        ([["ctrl", "info_x"], ["0", None]], True),
        ([["info_x"], ["5"]], False),
    ],
)
def test_regla_de_cero_por_filas_y_columnas(filas, esperado):
    assert evaluar(filas).ok is esperado


def test_motivo_es_la_columna_que_falla():
    assert evaluar([["ctrl"], ["1"]]).motivo == "ctrl"


def test_motivo_sin_fila_de_datos():
    assert evaluar([["ctrl"]]).motivo == "SIN_FILA_DE_DATOS"


def test_motivo_sin_columnas_de_control():
    assert evaluar([["info_x"], ["5"]]).motivo == "SIN_COLUMNAS_DE_CONTROL"


def test_columnas_convierten_enteros():
    assert evaluar([["ctrl", "info_filas"], ["0", "99"]]).columnas == {"ctrl": 0, "info_filas": 99}
