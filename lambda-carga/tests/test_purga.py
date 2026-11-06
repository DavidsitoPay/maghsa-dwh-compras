"""Purga: conserva los 14 runs mas recientes y lo referenciado; simulacion por defecto."""

import json

import pytest
import purga
from conftest import BASE_GLUE, BUCKET, CLAVE_ULTIMO, ErrorCliente, lineas_json
from errores import CargaError
from purga import DependenciasPurga
from runner import Config

PREFIJO_PREVIOS = "athena-results/etl/previos_"
LEGADO = f"s3://{BUCKET}/analytics/dim_proveedor/"


def run(n: int) -> str:
    return f"20260101{n:06d}"


@pytest.fixture
def deps_purga(s3, glue, sql_dir):
    config = Config(bucket=BUCKET, base=BASE_GLUE, workgroup="primary", sql_dir=sql_dir)
    return DependenciasPurga(s3=s3, glue=glue, config=config)


def sembrar_runs(s3, ids):
    for n in ids:
        s3.escribir_directo(f"analytics/runs/{run(n)}/dim_x/part.parquet", b"x")
        s3.escribir_directo(f"curated/runs/{run(n)}/c.parquet", b"y")


def sembrar_previo(s3, n, ubicacion=LEGADO):
    doc = {"schema": 1, "run_id": run(n), "tablas": {"dim_proveedor": {"location_previa": ubicacion}}}
    s3.escribir_directo(f"{PREFIJO_PREVIOS}{run(n)}.json", json.dumps(doc).encode("utf-8"))


def sembrar_escenario(s3, previos=range(1, 21), runs=range(1, 21)):
    sembrar_runs(s3, runs)
    for n in previos:
        sembrar_previo(s3, n)
    s3.escribir_directo(CLAVE_ULTIMO, json.dumps({"run_id": run(max(runs)), "tablas": {}}).encode("utf-8"))


def plan(capsys) -> dict:
    return next(r for r in lineas_json(capsys.readouterr().out) if r.get("evento") == "purga_plan")


def borrados(s3) -> set[str]:
    return {clave for lote in s3.llamadas_delete for clave in lote}


def ids_a_borrar(capsys) -> set[str]:
    return {entrada["run_id"] for entrada in plan(capsys)["a_borrar"]}


def test_conserva_los_14_mas_recientes(deps_purga, s3, capsys):
    sembrar_escenario(s3)
    purga.ejecutar_purga("simulacion", deps_purga)
    assert ids_a_borrar(capsys) == {run(n) for n in range(1, 7)}


def test_el_corte_es_el_run_14_mas_reciente(deps_purga, s3, capsys):
    sembrar_escenario(s3)
    purga.ejecutar_purga("simulacion", deps_purga)
    assert plan(capsys)["corte_run_id"] == run(7)


def test_menos_de_14_previos_no_borra_nada(deps_purga, s3, capsys):
    sembrar_escenario(s3, previos=range(1, 14))
    resultado = purga.ejecutar_purga("borrar", deps_purga)
    assert (resultado["estado"], s3.llamadas_delete) == ("sin_corte", [])


def test_protege_lo_referenciado_en_glue(deps_purga, s3, glue, capsys):
    sembrar_escenario(s3)
    glue.tablas["dim_proveedor"]["Location"] = f"s3://{BUCKET}/analytics/runs/{run(2)}/dim_proveedor/"
    glue.tablas["tmp_a_hechos"] = {"Location": f"s3://{BUCKET}/analytics/tmp/", "Parameters": {}}
    glue.particiones["tmp_a_hechos"] = [f"s3://{BUCKET}/analytics/runs/{run(3)}/hechos/"]
    purga.ejecutar_purga("simulacion", deps_purga)
    assert ids_a_borrar(capsys) == {run(1), run(4), run(5), run(6)}


def test_protege_el_ultimo_run(deps_purga, s3, capsys):
    sembrar_escenario(s3)
    s3.escribir_directo(
        CLAVE_ULTIMO,
        json.dumps({"run_id": run(20), "tablas": {"dim_proveedor": f"s3://{BUCKET}/analytics/runs/{run(1)}/"}}).encode(),
    )
    purga.ejecutar_purga("simulacion", deps_purga)
    assert run(1) not in ids_a_borrar(capsys)


def test_protege_la_ubicacion_previa_de_un_previo_retenido(deps_purga, s3, capsys):
    sembrar_escenario(s3)
    sembrar_previo(s3, 10, f"s3://{BUCKET}/analytics/runs/{run(4)}/dim_proveedor/")
    purga.ejecutar_purga("simulacion", deps_purga)
    assert run(4) not in ids_a_borrar(capsys)


def test_simulacion_no_llama_a_delete_objects(deps_purga, s3, capsys):
    sembrar_escenario(s3)
    purga.ejecutar_purga("simulacion", deps_purga)
    assert s3.llamadas_delete == []


def test_simulacion_registra_el_plan(deps_purga, s3, capsys):
    sembrar_escenario(s3)
    purga.ejecutar_purga("simulacion", deps_purga)
    assert plan(capsys)["modo"] == "simulacion"


def test_borrar_elimina_solo_los_runs_viejos(deps_purga, s3):
    sembrar_escenario(s3)
    purga.ejecutar_purga("borrar", deps_purga)
    esperados = {f"analytics/runs/{run(n)}/dim_x/part.parquet" for n in range(1, 7)}
    esperados |= {f"curated/runs/{run(n)}/c.parquet" for n in range(1, 7)}
    assert borrados(s3) == esperados


def test_borrar_registra_el_resultado(deps_purga, s3, capsys):
    sembrar_escenario(s3)
    purga.ejecutar_purga("borrar", deps_purga)
    resultado = next(r for r in lineas_json(capsys.readouterr().out) if r.get("evento") == "purga_resultado")
    assert resultado["borrados_objetos"] == 12


def test_nunca_borra_otros_prefijos(deps_purga, s3):
    sembrar_escenario(s3)
    otras = [
        "analytics/runs/2026010100001/x",
        "analytics/runs/abc/x",
        "managed/x",
        "analytics/dim_proveedor/part.parquet",
        "raw/compras/x.csv",
        "athena-results/etl/runs/x.json",
        "curated/entidad/x.parquet",
    ]
    for clave in otras:
        s3.escribir_directo(clave, b"z")
    purga.ejecutar_purga("borrar", deps_purga)
    assert not (borrados(s3) & set(otras))


def test_conjunto_vivo_vacio_aborta(deps_purga, s3, glue):
    sembrar_runs(s3, range(1, 21))
    for n in range(1, 21):
        sembrar_previo(s3, n)
    glue.tablas = {}
    with pytest.raises(CargaError) as excinfo:
        purga.ejecutar_purga("borrar", deps_purga)
    assert (excinfo.value.codigo, s3.llamadas_delete) == ("CONJUNTO_VIVO_VACIO", [])


def test_fallo_de_glue_aborta_sin_borrar(deps_purga, s3, glue):
    sembrar_escenario(s3)
    glue.fallar["get_tables"] = ErrorCliente("InternalFailure")
    with pytest.raises(ErrorCliente):
        purga.ejecutar_purga("borrar", deps_purga)
    assert s3.llamadas_delete == []


def test_previo_ilegible_aborta(deps_purga, s3):
    sembrar_escenario(s3)
    s3.escribir_directo(f"{PREFIJO_PREVIOS}{run(20)}.json", b"no es json")
    with pytest.raises(CargaError) as excinfo:
        purga.ejecutar_purga("simulacion", deps_purga)
    assert excinfo.value.codigo == "PREVIO_ILEGIBLE"


def test_tope_de_objetos_toma_los_mas_antiguos_primero(deps_purga, s3, capsys, monkeypatch):
    sembrar_escenario(s3)
    monkeypatch.setattr(purga, "TOPE_OBJETOS", 10)
    purga.ejecutar_purga("simulacion", deps_purga)
    assert [e["run_id"] for e in plan(capsys)["a_borrar"]] == [run(n) for n in range(1, 6)]


def test_lotes_de_mil_claves(deps_purga, s3):
    s3.tam_pagina = 1000
    sembrar_escenario(s3, previos=range(1, 16), runs=range(2, 16))
    for i in range(2500):
        s3.escribir_directo(f"analytics/runs/{run(1)}/dim_x/part-{i}.parquet", b"x")
    purga.ejecutar_purga("borrar", deps_purga)
    assert [len(lote) for lote in s3.llamadas_delete] == [1000, 1000, 500]


def test_revalida_la_clave_antes_de_borrar(deps_purga, s3, monkeypatch):
    sembrar_escenario(s3)
    monkeypatch.setattr(purga, "_objetos_run", lambda deps, run_id: iter([("managed/x", 1)]))
    with pytest.raises(CargaError) as excinfo:
        purga.ejecutar_purga("borrar", deps_purga)
    assert (excinfo.value.codigo, s3.llamadas_delete) == ("CLAVE_NO_PERMITIDA", [])


def test_modo_del_evento_no_cambia_el_modo_de_entorno(deps_purga, s3, monkeypatch):
    sembrar_escenario(s3)
    monkeypatch.setenv("PURGA_MODO", "simulacion")
    monkeypatch.setattr(purga, "crear_dependencias", lambda: deps_purga)
    purga.lambda_handler({"modo": "borrar"}, None)
    assert s3.llamadas_delete == []


def test_modo_vacio_es_invalido(deps_purga, s3, monkeypatch):
    monkeypatch.setenv("PURGA_MODO", "")
    monkeypatch.setattr(purga, "crear_dependencias", lambda: deps_purga)
    with pytest.raises(CargaError) as excinfo:
        purga.lambda_handler({}, None)
    assert excinfo.value.codigo == "PURGA_MODO_INVALIDO"


def test_errores_de_delete_objects_son_borrado_parcial(deps_purga, s3, capsys):
    sembrar_escenario(s3)
    s3.errores_delete = {"Key": f"analytics/runs/{run(1)}/dim_x/part.parquet", "Code": "AccessDenied"}
    with pytest.raises(CargaError) as excinfo:
        purga.ejecutar_purga("borrar", deps_purga)
    assert excinfo.value.codigo == "BORRADO_PARCIAL"


def test_clave_invalida_en_el_segundo_lote_no_borra_el_primero(deps_purga, s3, monkeypatch):
    sembrar_escenario(s3)
    validos = [(f"analytics/runs/{run(1)}/dim_x/part-{i}.parquet", 1) for i in range(1500)]

    def objetos_con_intruso(deps, run_id):
        return iter(validos + [("managed/x", 1)]) if run_id == run(1) else iter([])

    monkeypatch.setattr(purga, "_objetos_run", objetos_con_intruso)
    with pytest.raises(CargaError) as excinfo:
        purga.ejecutar_purga("borrar", deps_purga)
    assert (excinfo.value.codigo, s3.llamadas_delete) == ("CLAVE_NO_PERMITIDA", [])


def test_clave_de_run_protegido_no_se_borra(deps_purga, s3, glue, monkeypatch):
    sembrar_escenario(s3)
    glue.tablas["dim_proveedor"]["Location"] = f"s3://{BUCKET}/analytics/runs/{run(1)}/dim_proveedor/"
    monkeypatch.setattr(
        purga, "_objetos_run", lambda deps, run_id: iter([(f"analytics/runs/{run(1)}/dim_x/part.parquet", 1)])
    )
    with pytest.raises(CargaError) as excinfo:
        purga.ejecutar_purga("borrar", deps_purga)
    assert (excinfo.value.codigo, s3.llamadas_delete) == ("CLAVE_NO_PERMITIDA", [])


def test_protege_el_previo_de_ultimo_run(deps_purga, s3, capsys):
    sembrar_escenario(s3)
    s3.escribir_directo(
        CLAVE_ULTIMO,
        json.dumps({"run_id": run(20), "previo_run_id": run(1), "tablas": {}}).encode(),
    )
    purga.ejecutar_purga("simulacion", deps_purga)
    assert run(1) not in ids_a_borrar(capsys)


def test_fallo_de_get_partitions_aborta_sin_borrar(deps_purga, s3, glue):
    sembrar_escenario(s3)
    glue.fallar["get_partitions"] = ErrorCliente("InternalFailure")
    with pytest.raises(ErrorCliente):
        purga.ejecutar_purga("borrar", deps_purga)
    assert s3.llamadas_delete == []


def test_acceso_denegado_al_leer_ultimo_run_aborta_sin_borrar(deps_purga, s3, monkeypatch):
    sembrar_escenario(s3)
    listar = s3.list_objects_v2

    def listar_denegando_ultimo(Bucket, Prefix="", **resto):
        if Prefix == CLAVE_ULTIMO:
            raise ErrorCliente("AccessDenied")
        return listar(Bucket=Bucket, Prefix=Prefix, **resto)

    monkeypatch.setattr(s3, "list_objects_v2", listar_denegando_ultimo)
    with pytest.raises(ErrorCliente):
        purga.ejecutar_purga("borrar", deps_purga)
    assert s3.llamadas_delete == []


def test_paginacion_de_particiones_protege_el_run_de_la_segunda_pagina(deps_purga, s3, glue, capsys):
    sembrar_escenario(s3)
    glue.particiones["dim_proveedor"] = [
        f"s3://{BUCKET}/analytics/dim_proveedor/",
        f"s3://{BUCKET}/analytics/runs/{run(2)}/dim_proveedor/",
    ]
    purga.ejecutar_purga("simulacion", deps_purga)
    assert run(2) not in ids_a_borrar(capsys)


def test_sin_ultimo_run_protege_lo_que_glue_referencia(deps_purga, s3, glue, capsys):
    sembrar_escenario(s3)
    s3.objetos.pop(CLAVE_ULTIMO)
    glue.tablas["dim_proveedor"]["Location"] = f"s3://{BUCKET}/analytics/runs/{run(2)}/dim_proveedor/"
    purga.ejecutar_purga("simulacion", deps_purga)
    assert run(2) not in ids_a_borrar(capsys)


def test_catorce_previos_exactos_fijan_el_corte_sin_borrar(deps_purga, s3, capsys):
    sembrar_escenario(s3, previos=range(1, 15))
    purga.ejecutar_purga("borrar", deps_purga)
    assert (plan(capsys)["corte_run_id"], s3.llamadas_delete) == (run(1), [])


def test_prefijos_hermanos_de_un_run_no_se_borran(deps_purga, s3):
    sembrar_escenario(s3)
    hermanos = [f"analytics/runs/{run(1)}0/x", f"analytics/runs/{run(1)}-bak/x"]
    for clave in hermanos:
        s3.escribir_directo(clave, b"z")
    purga.ejecutar_purga("borrar", deps_purga)
    assert not (borrados(s3) & set(hermanos))


def test_tope_en_modo_borrar_deja_el_resto_en_el_bucket(deps_purga, s3, monkeypatch):
    sembrar_escenario(s3)
    monkeypatch.setattr(purga, "TOPE_OBJETOS", 10)
    purga.ejecutar_purga("borrar", deps_purga)
    esperados = {f"analytics/runs/{run(n)}/dim_x/part.parquet" for n in range(1, 6)}
    esperados |= {f"curated/runs/{run(n)}/c.parquet" for n in range(1, 6)}
    assert borrados(s3) == esperados


def test_error_en_el_primer_lote_corta_los_siguientes(deps_purga, s3, capsys):
    sembrar_escenario(s3, previos=range(1, 16), runs=range(2, 16))
    s3.tam_pagina = 1000
    for i in range(2500):
        s3.escribir_directo(f"analytics/runs/{run(1)}/dim_x/part-{i}.parquet", b"x")
    s3.errores_delete = {"Key": f"analytics/runs/{run(1)}/dim_x/part-0.parquet", "Code": "AccessDenied"}
    with pytest.raises(CargaError) as excinfo:
        purga.ejecutar_purga("borrar", deps_purga)
    resultado = next(r for r in lineas_json(capsys.readouterr().out) if r.get("evento") == "purga_resultado")
    assert (excinfo.value.codigo, len(s3.llamadas_delete), len(resultado["errores"])) == ("BORRADO_PARCIAL", 1, 1)


def test_previo_15_no_protege_y_previo_14_si(deps_purga, s3, capsys):
    sembrar_escenario(s3)
    sembrar_previo(s3, 6, f"s3://{BUCKET}/analytics/runs/{run(2)}/dim_proveedor/")
    sembrar_previo(s3, 7, f"s3://{BUCKET}/analytics/runs/{run(3)}/dim_proveedor/")
    purga.ejecutar_purga("simulacion", deps_purga)
    a_borrar = ids_a_borrar(capsys)
    assert (run(2) in a_borrar, run(3) in a_borrar) == (True, False)


def test_previos_basura_no_cuentan_para_las_14_corridas(deps_purga, s3):
    sembrar_escenario(s3, previos=range(1, 14))
    s3.escribir_directo(f"{PREFIJO_PREVIOS}abc.json", b"{}")
    s3.escribir_directo(f"{PREFIJO_PREVIOS}{run(14)}.json.bak", b"{}")
    resultado = purga.ejecutar_purga("borrar", deps_purga)
    assert (resultado["estado"], s3.llamadas_delete) == ("sin_corte", [])


@pytest.mark.parametrize("valor", ["BORRAR", "Borrar", "borrar "])
def test_modo_con_mayusculas_o_espacios_es_invalido(deps_purga, s3, monkeypatch, valor):
    sembrar_escenario(s3)
    monkeypatch.setenv("PURGA_MODO", valor)
    monkeypatch.setattr(purga, "crear_dependencias", lambda: deps_purga)
    with pytest.raises(CargaError) as excinfo:
        purga.lambda_handler({}, None)
    assert (excinfo.value.codigo, s3.llamadas_delete) == ("PURGA_MODO_INVALIDO", [])


def test_vista_sin_particiones_no_aborta_ni_se_consulta(deps_purga, s3, glue, capsys):
    sembrar_escenario(s3)
    glue.sembrar_vista("v_compras", f"s3://{BUCKET}/analytics/vistas/v_compras/")
    resultado = purga.ejecutar_purga("borrar", deps_purga)
    assert (
        resultado["estado"],
        borrados(s3) == {f"analytics/runs/{run(n)}/dim_x/part.parquet" for n in range(1, 7)}
        | {f"curated/runs/{run(n)}/c.parquet" for n in range(1, 7)},
        "v_compras" in glue.consultas_particiones,
    ) == ("borrado", True, False)


def test_ubicacion_de_vista_no_protege_runs(deps_purga, s3, glue, capsys):
    sembrar_escenario(s3)
    glue.sembrar_vista("v_compras", f"s3://{BUCKET}/analytics/runs/{run(2)}/v_compras/")
    purga.ejecutar_purga("simulacion", deps_purga)
    assert ids_a_borrar(capsys) == {run(n) for n in range(1, 7)}
