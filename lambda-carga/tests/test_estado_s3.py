"""EstadoS3 y leer_objeto: una clave ausente nunca se interpreta por un 403 del GET (R6)."""

from conftest import CLAVE_ULTIMO
from estado_s3 import EstadoS3, leer_objeto
from conftest import BUCKET


def test_leer_json_ausente_es_none(s3):
    assert EstadoS3(s3, BUCKET).leer_json(CLAVE_ULTIMO) is None


def test_leer_json_ausente_con_403_en_get_es_none(s3):
    s3.ausente_da_403 = True
    assert EstadoS3(s3, BUCKET).leer_json(CLAVE_ULTIMO) is None


def test_leer_json_presente_devuelve_el_documento(s3):
    s3.escribir_directo(CLAVE_ULTIMO, b'{"run_id": "20261104120000"}')
    assert EstadoS3(s3, BUCKET).leer_json(CLAVE_ULTIMO) == {"run_id": "20261104120000"}


def test_leer_objeto_con_clave_ausente_no_llama_get(s3, monkeypatch):
    llamadas = []
    monkeypatch.setattr(s3, "get_object", lambda **kwargs: llamadas.append(kwargs))
    leer_objeto(s3, BUCKET, CLAVE_ULTIMO)
    assert llamadas == []
