"""LockS3: escrituras condicionales, lock vencido, ilegible, carrera y perdida del lock."""

import pytest
from conftest import BUCKET, CLAVE_LOCK, FakeS3, cuerpo_lock, lineas_json
from errores import CargaError
from lock_s3 import LockS3, soporta_if_match

RUN = "20261104120000"


@pytest.fixture
def lock(s3, reloj):
    return LockS3(s3, BUCKET, reloj)


def test_lock_ausente_se_crea_con_if_none_match(lock, s3):
    assert lock.adquirir() is True and s3.puts[-1]["IfNoneMatch"] == "*"


def test_lock_libre_se_toma_con_if_match(lock, s3):
    s3.escribir_directo(CLAVE_LOCK, cuerpo_lock("free", 0))
    etag = s3.objetos[CLAVE_LOCK][1]
    lock.adquirir()
    assert s3.puts[-1]["IfMatch"] == etag


def test_lock_vencido_se_toma(lock, s3):
    s3.escribir_directo(CLAVE_LOCK, cuerpo_lock("busy", -10, "vieja"))
    assert lock.adquirir() is True


def test_lock_vigente_ocupado_devuelve_false(lock, s3):
    s3.escribir_directo(CLAVE_LOCK, cuerpo_lock("busy", 600, "otra"))
    assert lock.adquirir() is False


def test_carrera_en_el_put_devuelve_false(lock, s3):
    s3.escribir_directo(CLAVE_LOCK, cuerpo_lock("free", 0))
    s3.antes_de_put = lambda fake: fake.escribir_directo(CLAVE_LOCK, cuerpo_lock("busy", 600, "otra"))
    assert lock.adquirir() is False


def test_if_match_sobre_clave_borrada_devuelve_false(lock, s3):
    s3.escribir_directo(CLAVE_LOCK, cuerpo_lock("free", 0))
    s3.antes_de_put = lambda fake: fake.objetos.pop(CLAVE_LOCK)
    assert lock.adquirir() is False


def test_lock_ilegible_se_trata_como_vencido(lock, s3):
    s3.escribir_directo(CLAVE_LOCK, b"no es json")
    assert lock.adquirir() is True


def test_lock_ilegible_registra_el_evento(lock, s3, capsys):
    s3.escribir_directo(CLAVE_LOCK, b"no es json")
    lock.adquirir()
    assert any(linea["evento"] == "lock_ilegible" for linea in lineas_json(capsys.readouterr().out))


def test_renovar_con_412_lanza_lock_perdido(lock, s3):
    lock.adquirir()
    s3.escribir_directo(CLAVE_LOCK, cuerpo_lock("free", 0))
    with pytest.raises(CargaError) as excinfo:
        lock.renovar(RUN)
    assert excinfo.value.codigo == "LOCK_PERDIDO"


def test_liberar_con_412_solo_registra(lock, s3, capsys):
    lock.adquirir()
    s3.escribir_directo(CLAVE_LOCK, cuerpo_lock("free", 0))
    lock.liberar()
    assert any(linea["evento"] == "lock_liberacion_412" for linea in lineas_json(capsys.readouterr().out))


def test_ausente_con_403_en_get_se_crea_igual(lock, s3):
    s3.ausente_da_403 = True
    assert lock.adquirir() is True


def test_soporte_if_match_true_con_s3_moderno(s3):
    assert soporta_if_match(s3) is True


def test_soporte_if_match_false_sin_condicionales(s3):
    s3.soporta_condicionales = False
    assert soporta_if_match(s3) is False
