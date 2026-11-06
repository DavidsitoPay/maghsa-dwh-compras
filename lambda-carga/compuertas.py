"""Compuertas de validacion: una fila de datos con columnas de control en cero.

Las columnas `info_*` solo se registran; no validan.
"""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

PREFIJO_INFO = "info_"


@dataclass(frozen=True)
class ResultadoCompuerta:
    ok: bool
    columnas: dict[str, int | float | str | None]
    motivo: str | None


def evaluar(filas: list[list[str | None]]) -> ResultadoCompuerta:
    if len(filas) != 2:
        return ResultadoCompuerta(False, {}, "SIN_FILA_DE_DATOS")
    encabezado, datos = filas
    crudos = dict(zip(encabezado, datos))
    columnas = {nombre: _convertir(valor) for nombre, valor in crudos.items()}
    de_control = [nombre for nombre in encabezado if not nombre.startswith(PREFIJO_INFO)]
    if not de_control:
        return ResultadoCompuerta(False, columnas, "SIN_COLUMNAS_DE_CONTROL")
    for nombre in de_control:
        if not _es_cero(crudos[nombre]):
            return ResultadoCompuerta(False, columnas, nombre)
    return ResultadoCompuerta(True, columnas, None)


def _convertir(valor: str | None) -> int | float | str | None:
    if valor is None:
        return None
    try:
        numero = Decimal(valor)
    except InvalidOperation:
        return valor
    if numero.is_finite() and numero == numero.to_integral_value():
        return int(numero)
    return float(numero)


def _es_cero(valor: str | None) -> bool:
    if valor is None:
        return False
    try:
        numero = Decimal(valor)
    except InvalidOperation:
        return False
    return numero.is_finite() and numero == 0
