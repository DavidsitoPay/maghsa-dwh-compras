import io
import os
import sys
import types
from datetime import date
from pathlib import Path

import pytest

os.environ["BUCKET_NAME"] = "bucket-de-prueba"
os.environ["ACCESS_CODE"] = "codigo-de-prueba"


class NoSuchKey(Exception):
    pass


class S3Falso:
    exceptions = types.SimpleNamespace(NoSuchKey=NoSuchKey)

    def __init__(self):
        self.objetos = {}
        self.fallar_listado = False

    def get_object(self, Bucket, Key):
        if Key not in self.objetos:
            raise NoSuchKey(Key)
        return {"Body": io.BytesIO(self.objetos[Key])}

    def put_object(self, Bucket, Key, Body):
        self.objetos[Key] = Body

    def get_paginator(self, _operacion):
        return self

    def paginate(self, Bucket, Prefix):
        if self.fallar_listado:
            raise RuntimeError("AccessDenied")
        for clave in sorted(k for k in self.objetos if k.startswith(Prefix)):
            yield {"Contents": [{"Key": clave}]}
        yield {}


S3_FALSO = S3Falso()
sys.modules["boto3"] = types.SimpleNamespace(client=lambda *_: S3_FALSO)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import lambda_function  # noqa: E402


def _poner(ruta, columnas, *filas):
    lambda_function._escribir_csv(ruta, columnas, [dict(zip(columnas, f)) for f in filas])


def _sembrar():
    lf = lambda_function
    R, C = lf.RUTAS, lf.COLUMNAS
    _poner(R["categorias"], C["categorias"],
           ("CAT01", "Repuestos", "Mantenimiento"), ("CAT02", "Aceites", "Mantenimiento"), ("CAT03", "Sin uso", "Operacion"))
    _poner(R["categorias_proveedor"], C["categorias_proveedor"],
           ("CATPROV01", "Repuestos", ""), ("CATPROV02", "Combustibles", ""), ("CATPROV03", "Sin uso", ""))
    _poner(R["unidades_organizacionales"], C["unidades_organizacionales"],
           ("UO01", "Mantenimiento"), ("UO02", "Produccion"), ("UO03", "Operacion"))
    _poner(R["productos"], C["productos"],
           ("PROD001", "Filtro", "CAT01", "unidad", ""), ("PROD002", "Aceite", "CAT02", "galon", ""),
           ("PROD003", "Sin uso", "CAT01", "unidad", ""))
    _poner(R["proveedores"], C["proveedores"],
           ("PRV001", "Alfa", "Guatemala", "Guatemala", "30 dias", "vigente"),
           ("PRV002", "Beta", "Guatemala", "Escuintla", "contado", "vigente"),
           ("PRV003", "Sin uso", "Guatemala", "", "45 dias", "inactivo"))
    _poner(lf.RUTA_PROVEEDOR_X_PRODUCTO, lf.COLUMNAS_PROVEEDOR_X_PRODUCTO,
           ("PRV001", "PROD001"), ("PRV002", "PROD002"))
    _poner(lf.RUTA_PROVEEDOR_CATEGORIA_PROVEEDOR, lf.COLUMNAS_PROVEEDOR_CATEGORIA_PROVEEDOR,
           ("PRV001", "CATPROV01"), ("PRV002", "CATPROV02"))
    _poner(lf.RUTA_PROVEEDOR_CATEGORIA_PRODUCTO, lf.COLUMNAS_PROVEEDOR_CATEGORIA_PRODUCTO,
           ("PRV001", "CAT01"), ("PRV002", "CAT02"))
    _poner(lf.RUTA_CATEGORIA_PROVEEDOR_X_CATEGORIA_PRODUCTO, lf.COLUMNAS_CATEGORIA_PROVEEDOR_X_CATEGORIA_PRODUCTO,
           ("CATPROV01", "CAT01"), ("CATPROV02", "CAT02"))
    _poner(lf.RUTA_CONTACTO_PROVEEDOR, lf.COLUMNAS_CONTACTO_PROVEEDOR,
           ("PRV001", "Ana", "5555-0000", "ana@alfa.gt"))
    _poner(R["compras"], C["compras"],
           ("OCW0001", "2026-10-01", "PRV001", "PROD001", "CAT01", "UO01", "2", "10", "GTQ", "30 dias", "5"))
    _poner("raw/compras/anio=2026/mes=10/registro_compras.csv", C["compras"],
           ("OC0001", "2026-10-02", "PRV002", "PROD002", "CAT02", "UO02", "1", "5", "GTQ", "contado", "3"))


@pytest.fixture
def lf(monkeypatch):
    S3_FALSO.fallar_listado = False
    S3_FALSO.objetos.clear()
    _sembrar()
    monkeypatch.setattr(lambda_function, "_hoy_guatemala", lambda: date(2026, 11, 3))
    return lambda_function
