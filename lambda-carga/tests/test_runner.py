"""Corrida completa de runner.ejecutar_corrida con Athena, S3 y Glue falsos."""

import re

import athena_ejecutor
import pytest
from conftest import (
    BUCKET,
    CLAVE_LOCK,
    CLAVE_ULTIMO,
    PREFIJO_PREVIOS,
    RUN_BASE,
    cuerpo_lock,
    cuerpo_ultimo_run,
    lineas_json,
)
from errores import CargaError
from runner import ejecutar_corrida
from tablas import HECHOS, TABLAS_VIVAS

PREVIO_INICIAL = "20260101000000"
FORWARD_11 = [tabla for tabla in TABLAS_VIVAS if tabla != HECHOS]
LEGADO = {tabla: f"s3://{BUCKET}/analytics/{tabla}/" for tabla in TABLAS_VIVAS}
ALTER_EN_RUN = f"SET LOCATION 's3://{BUCKET}/analytics/runs/"


def correr(deps, evento=None):
    return ejecutar_corrida(evento or {}, deps)


def correr_fallida(deps, evento=None):
    with pytest.raises(CargaError) as excinfo:
        ejecutar_corrida(evento or {}, deps)
    return excinfo.value


def sentencias(athena):
    return [inicio["sql"] for inicio in athena.inicios]


def ids_de_corrida(athena):
    ids = []
    for token in athena.intentos_inicio:
        run_id = token.split("-")[2]
        if run_id not in ids:
            ids.append(run_id)
    return ids


def alter_en_run(athena):
    return [sql for sql in sentencias(athena) if ALTER_EN_RUN in sql]


def alters_de_rollback(athena):
    return [
        sql.split()[2]
        for sql in sentencias(athena)
        if sql.startswith("ALTER TABLE") and "/runs/" not in sql
    ]


def lineas(capsys):
    return lineas_json(capsys.readouterr().out)


def registros(capsys, nombre):
    return [linea for linea in lineas(capsys) if linea.get("evento") == nombre]


def sembrar_ultimo(s3, run_id=PREVIO_INICIAL):
    s3.escribir_directo(CLAVE_ULTIMO, cuerpo_ultimo_run(run_id))


def ubicaciones_glue(glue):
    return {tabla: glue.ubicacion(tabla).rstrip("/") for tabla in TABLAS_VIVAS}


def ubicaciones_run(run_id):
    return {tabla: f"s3://{BUCKET}/analytics/runs/{run_id}/{tabla}" for tabla in TABLAS_VIVAS}


# --- Compra nueva (OCW0002) -------------------------------------------------------------

def test_compra_nueva_devuelve_estado_ok(deps, s3):
    sembrar_ultimo(s3)
    assert correr(deps)["estado"] == "ok"


def test_compra_nueva_apunta_las_12_tablas_al_run_nuevo(deps, glue, s3):
    sembrar_ultimo(s3)
    correr(deps)
    assert ubicaciones_glue(glue) == ubicaciones_run(RUN_BASE)


def test_compra_nueva_publica_11_alter_mas_hechos(deps, athena, s3):
    sembrar_ultimo(s3)
    correr(deps)
    assert len(alter_en_run(athena)) == len(TABLAS_VIVAS)


def test_compra_nueva_tokens_contiguos_y_unicos(deps, athena, s3):
    sembrar_ultimo(s3)
    correr(deps)
    esperados = [f"maghsa-carga-{RUN_BASE}-{n:05d}" for n in range(1, len(athena.inicios) + 1)]
    assert [inicio["token"] for inicio in athena.inicios] == esperados


def test_compra_nueva_orden_de_ejecucion(deps, athena, s3):
    sembrar_ultimo(s3)
    correr(deps)
    sql = sentencias(athena)
    posicion = {
        "g2_fk": next(i for i, s in enumerate(sql) if "g2_fk" in s),
        "07d": next(i for i, s in enumerate(sql) if s.startswith("INSERT INTO tmp_a_hechos")),
        "14": next(i for i, s in enumerate(sql) if f"ALTER TABLE dim_proveedor {ALTER_EN_RUN}" in s),
        "14p": next(i for i, s in enumerate(sql) if s.startswith(f"ALTER TABLE {HECHOS} {ALTER_EN_RUN}")),
        "15": next(i for i, s in enumerate(sql) if "g15_publicacion" in s),
        "99": next(i for i, s in enumerate(sql) if "DROP VIEW IF EXISTS tmp_v_compras" in s),
    }
    assert sorted(posicion, key=posicion.get) == ["07d", "g2_fk", "14", "14p", "15", "99"]


def test_tokens_cumplen_formato_y_longitud_de_athena(deps, athena, s3):
    sembrar_ultimo(s3)
    correr(deps)
    tokens = [inicio["token"] for inicio in athena.inicios]
    assert all(re.fullmatch(r"maghsa-carga-\d{14}-\d{5}", t) and 32 <= len(t) <= 128 for t in tokens)


def test_compra_nueva_previos_se_escriben_antes_del_primer_alter(deps, eventos, s3):
    sembrar_ultimo(s3)
    correr(deps)
    indice_previos = eventos.index(("put", f"{PREFIJO_PREVIOS}{RUN_BASE}.json"))
    indice_alter = next(i for i, e in enumerate(eventos) if e[0] == "athena" and ALTER_EN_RUN in e[1])
    assert indice_previos < indice_alter


def test_compra_nueva_previos_guardan_ubicacion_legado(deps, s3):
    sembrar_ultimo(s3)
    correr(deps)
    previos = s3.leer(f"{PREFIJO_PREVIOS}{RUN_BASE}.json")
    assert {t: v["location_previa"] for t, v in previos["tablas"].items()} == LEGADO


def test_compra_nueva_ultimo_run_describe_la_corrida(deps, s3):
    sembrar_ultimo(s3)
    correr(deps)
    doc = s3.leer(CLAVE_ULTIMO)
    assert (doc["run_id"], doc["estado"], doc["intentos"], doc["hechos_modo"]) == (
        RUN_BASE, "ok", 1, "proyeccion",
    )


def test_compra_nueva_ultimo_run_registra_filas_y_previo(deps, s3):
    sembrar_ultimo(s3)
    correr(deps)
    doc = s3.leer(CLAVE_ULTIMO)
    assert (doc["filas_hechos"], doc["previo_run_id"]) == (99, PREVIO_INICIAL)


def test_compra_nueva_ultimo_run_lista_las_12_tablas(deps, s3):
    sembrar_ultimo(s3)
    correr(deps)
    assert set(s3.leer(CLAVE_ULTIMO)["tablas"]) == set(TABLAS_VIVAS)


def test_compra_nueva_99_corre_despues_de_ultimo_run(deps, eventos, s3):
    sembrar_ultimo(s3)
    correr(deps)
    indice_ultimo = eventos.index(("put", CLAVE_ULTIMO))
    indice_limpieza = next(i for i, e in enumerate(eventos) if e[0] == "athena" and "tmp_v_compras" in e[1])
    assert indice_limpieza > indice_ultimo


def test_compra_nueva_escribe_log_de_la_corrida(deps, s3):
    sembrar_ultimo(s3)
    correr(deps)
    assert s3.leer(f"athena-results/etl/runs/{RUN_BASE}.json")["estado"] == "ok"


def test_compra_nueva_deja_el_lock_libre(deps, s3):
    sembrar_ultimo(s3)
    correr(deps)
    assert s3.leer(CLAVE_LOCK)["estado"] == "free"


def test_compra_nueva_registra_sentencias_con_campos(deps, s3, capsys):
    sembrar_ultimo(s3)
    correr(deps)
    primera = registros(capsys, "sentencia")[0]
    assert {"run_id", "intento", "archivo", "indice", "tipo", "estado"} <= primera.keys()


# --- Maestro renombrado y corridas repetidas ---------------------------------------------

def test_maestro_renombrado_todas_las_compuertas_pasan(deps, s3, capsys):
    sembrar_ultimo(s3)
    correr(deps)
    ids_ok = {r["id"] for r in registros(capsys, "compuerta") if r["resultado"] == "ok"}
    assert ids_ok == {"G1", "G2.fk", "G2.conteo", "G2.tiempo", "G2.rango", "G3", "G15"}


def test_corrida_doble_encadena_previo_y_runs(deps, s3, reloj):
    sembrar_ultimo(s3)
    primera = correr(deps)
    reloj.avanzar(60)
    segunda = correr(deps)
    doc = s3.leer(CLAVE_ULTIMO)
    assert (doc["run_id"], doc["previo_run_id"]) == (segunda["run_id"], primera["run_id"])


def test_corrida_doble_previos_guardan_la_ubicacion_de_la_primera(deps, s3, reloj):
    sembrar_ultimo(s3)
    primera = correr(deps)
    reloj.avanzar(60)
    segunda = correr(deps)
    previos = s3.leer(f"{PREFIJO_PREVIOS}{segunda['run_id']}.json")
    assert previos["tablas"]["dim_proveedor"]["location_previa"].rstrip("/") == (
        f"s3://{BUCKET}/analytics/runs/{primera['run_id']}/dim_proveedor"
    )


@pytest.mark.xfail(
    strict=True,
    reason="generar_run_id solo evita repetir el run_id dentro de una invocacion; "
    "dos corridas en el mismo segundo reciben el mismo run_id (defecto abierto, ver impl-T8-tests.md)",
)
def test_run_id_nuevo_aunque_mismo_segundo(deps, s3):
    sembrar_ultimo(s3)
    primera = correr(deps)
    segunda = correr(deps)
    assert primera["run_id"] != segunda["run_id"]


# --- Lock -------------------------------------------------------------------------------

def test_lock_vigente_omite_sin_llamar_a_athena_ni_glue(deps, s3, athena, glue):
    s3.escribir_directo(CLAVE_LOCK, cuerpo_lock("busy", 600, "otra"))
    assert (correr(deps)["estado"], athena.intentos_inicio, glue.llamadas) == ("omitida", [], [])


def test_lock_vigente_no_emite_metricas_emf(deps, s3, capsys):
    s3.escribir_directo(CLAVE_LOCK, cuerpo_lock("busy", 600, "otra"))
    correr(deps)
    assert not [linea for linea in lineas(capsys) if "_aws" in linea]


def test_lock_vencido_se_toma_y_corre(deps, s3):
    s3.escribir_directo(CLAVE_LOCK, cuerpo_lock("busy", -10, "vieja"))
    assert correr(deps)["estado"] == "ok"


def test_carrera_en_el_lock_omite_la_corrida(deps, s3, athena):
    s3.escribir_directo(CLAVE_LOCK, cuerpo_lock("free", 0))
    s3.antes_de_put = lambda fake: fake.escribir_directo(CLAVE_LOCK, cuerpo_lock("busy", 600, "otra"))
    assert (correr(deps)["estado"], athena.intentos_inicio) == ("omitida", [])


def test_lock_se_libera_aunque_falle_la_corrida(deps, s3, athena):
    sembrar_ultimo(s3)
    athena.programar_compuerta("g1_duplicados", {"ctrl": "1", "info_filas": "99"})
    correr_fallida(deps)
    assert s3.leer(CLAVE_LOCK)["estado"] == "free"


def test_sin_if_match_aborta_antes_de_todo(deps, s3, athena):
    s3.soporta_condicionales = False
    error = correr_fallida(deps)
    assert (error.codigo, s3.puts, athena.intentos_inicio) == ("LOCK_NO_SOPORTADO", [], [])


def test_workgroup_con_enforce_aborta_y_libera(deps, s3, athena):
    athena.enforce = True
    error = correr_fallida(deps)
    assert (error.codigo, athena.inicios, s3.leer(CLAVE_LOCK)["estado"]) == (
        "WORKGROUP_ENFORCE", [], "free",
    )


def test_workgroup_con_enforce_no_escribe_previos(deps, s3, athena):
    athena.enforce = True
    correr_fallida(deps)
    assert s3.claves(PREFIJO_PREVIOS) == set()


def test_workgroup_sin_bloque_configuration_no_aborta(deps, athena, monkeypatch):
    monkeypatch.setattr(athena, "get_work_group", lambda WorkGroup: {"WorkGroup": {}})
    assert correr(deps)["estado"] == "ok"


@pytest.mark.parametrize(
    "evento",
    [{"run_id": "x"}, {"forzar_g3": "si"}, {"otro": 1}, ["forzar_g3"]],
)
def test_evento_invalido_no_toca_nada(deps, s3, evento):
    assert correr_fallida(deps, evento).codigo == "EVENTO_INVALIDO" and s3.puts == []


def test_evento_forzar_g3_booleano_es_valido(deps, s3):
    sembrar_ultimo(s3)
    assert correr(deps, {"forzar_g3": False})["estado"] == "ok"


# --- Compuertas y reintentos ------------------------------------------------------------

def test_g1_fallida_corta_antes_de_07c(deps, athena, glue, s3):
    sembrar_ultimo(s3)
    athena.programar_compuerta("g1_duplicados", {"ctrl": "1", "info_filas": "99"})
    error = correr_fallida(deps)
    assert (error.codigo, any("tmp_a_hechos_07c" in s for s in sentencias(athena))) == (
        "COMPUERTA_FALLIDA", False,
    )


def test_g1_fallida_no_altera_el_dato_vivo(deps, athena, glue, s3):
    sembrar_ultimo(s3)
    athena.programar_compuerta("g1_duplicados", {"ctrl": "1", "info_filas": "99"})
    correr_fallida(deps)
    assert (ubicaciones_glue(glue) == {t: v.rstrip("/") for t, v in LEGADO.items()}, alter_en_run(athena)) == (
        True, [],
    )


def test_g1_fallida_no_reintenta(deps, athena, s3):
    sembrar_ultimo(s3)
    athena.programar_compuerta("g1_duplicados", {"ctrl": "1", "info_filas": "99"})
    correr_fallida(deps)
    assert len(ids_de_corrida(athena)) == 1


def test_g1_fallida_conserva_ultimo_run(deps, athena, s3):
    sembrar_ultimo(s3)
    athena.programar_compuerta("g1_duplicados", {"ctrl": "1", "info_filas": "99"})
    correr_fallida(deps)
    assert s3.leer(CLAVE_ULTIMO)["run_id"] == PREVIO_INICIAL


def test_g1_fallida_ejecuta_99(deps, athena, s3):
    sembrar_ultimo(s3)
    athena.programar_compuerta("g1_duplicados", {"ctrl": "1", "info_filas": "99"})
    correr_fallida(deps)
    assert any("tmp_v_compras" in s for s in sentencias(athena))


def test_g1_fallida_emf_run_ok_cero(deps, athena, s3, capsys):
    sembrar_ultimo(s3)
    athena.programar_compuerta("g1_duplicados", {"ctrl": "1", "info_filas": "99"})
    correr_fallida(deps)
    emf = [linea for linea in lineas(capsys) if "_aws" in linea][0]
    assert emf["RunOK"] == 0


def test_g1_fallida_registra_columnas_de_la_compuerta(deps, athena, s3, capsys):
    sembrar_ultimo(s3)
    athena.programar_compuerta("g1_duplicados", {"ctrl": "1", "info_filas": "99"})
    correr_fallida(deps)
    falla = [r for r in registros(capsys, "compuerta") if r["id"] == "G1"][0]
    assert falla["columnas"] == {"ctrl": 1, "info_filas": 99}


def test_g2_fk_reintenta_una_vez_con_run_y_tokens_nuevos(deps, athena, s3):
    sembrar_ultimo(s3)
    athena.programar_compuerta("g2_fk", {"ctrl": "1"}, veces=1)
    res = correr(deps)
    primer, segundo = ids_de_corrida(athena)
    assert (res["intentos"], res["run_id"]) == (2, segundo) and primer != segundo


def test_g2_fk_reintento_deja_log_del_primer_intento_fallido(deps, athena, s3):
    sembrar_ultimo(s3)
    athena.programar_compuerta("g2_fk", {"ctrl": "1"}, veces=1)
    correr(deps)
    primer = ids_de_corrida(athena)[0]
    assert s3.leer(f"athena-results/etl/runs/{primer}.json")["estado"] == "fallo"


def test_reintento_maximo_una_vez(deps, athena, s3):
    sembrar_ultimo(s3)
    athena.programar_compuerta("g2_conteo", {"ctrl": "1"})
    error = correr_fallida(deps)
    assert (error.codigo, len(ids_de_corrida(athena))) == ("COMPUERTA_FALLIDA", 2)


def test_no_reintenta_si_restan_menos_de_420_s(deps, athena, s3):
    sembrar_ultimo(s3)
    athena.programar_costo("g2_fk", 430)
    athena.programar_compuerta("g2_fk", {"ctrl": "1"})
    correr_fallida(deps)
    assert len(ids_de_corrida(athena)) == 1


def test_reintenta_si_restan_420_s_exactos(deps, athena, s3):
    sembrar_ultimo(s3)
    athena.programar_costo("g2_fk", 420, veces=1)
    athena.programar_compuerta("g2_fk", {"ctrl": "1"}, veces=1)
    assert correr(deps)["intentos"] == 2


def test_error_system_reintenta_y_termina_ok(deps, athena, s3):
    sembrar_ultimo(s3)
    athena.programar_falla("tmp_a_hechos_07c", 1, veces=1)
    assert correr(deps)["estado"] == "ok"


def test_error_user_no_reintenta(deps, athena, s3):
    sembrar_ultimo(s3)
    athena.programar_falla("tmp_a_hechos_07c", 2, veces=1)
    correr_fallida(deps)
    assert len(ids_de_corrida(athena)) == 1


@pytest.mark.parametrize("patron", ["g2_tiempo", "g2_rango", "g1_duplicados"])
def test_compuerta_no_reintentable_no_reintenta(deps, athena, s3, patron):
    sembrar_ultimo(s3)
    athena.programar_compuerta(patron, {"ctrl": "1", "info_filas": "99"})
    correr_fallida(deps)
    assert len(ids_de_corrida(athena)) == 1


def test_g3_fallida_corta_y_no_publica(deps, athena, s3, glue):
    sembrar_ultimo(s3)
    athena.programar_compuerta("g3_nuevo", {"ctrl": "1", "info_filas_nuevo": "99"})
    error = correr_fallida(deps)
    assert (error.codigo, alter_en_run(athena), ubicaciones_glue(glue)) == (
        "COMPUERTA_FALLIDA", [], {t: v.rstrip("/") for t, v in LEGADO.items()},
    )


def test_g3_forzada_publica_y_registra_forzada(deps, athena, s3, capsys):
    sembrar_ultimo(s3)
    athena.programar_compuerta("g3_nuevo", {"ctrl": "1", "info_filas_nuevo": "99"})
    res = correr(deps, {"forzar_g3": True})
    forzada = [r for r in registros(capsys, "compuerta") if r["id"] == "G3"][0]
    assert (res["estado"], forzada["forzada"]) == ("ok", True)


def test_forzar_g3_no_omite_g2_tiempo(deps, athena, s3):
    sembrar_ultimo(s3)
    athena.programar_compuerta("g2_tiempo", {"ctrl": "1"})
    assert correr_fallida(deps, {"forzar_g3": True}).codigo == "COMPUERTA_FALLIDA"


# --- Caidas, rollback y publicacion -----------------------------------------------------

def test_caida_en_07c_conserva_ultimo_run_y_libera(deps, athena, s3, reloj):
    primera = correr(deps)
    reloj.avanzar(60)
    athena.programar_falla("tmp_a_hechos_07c", 2, veces=1)
    correr_fallida(deps)
    assert (s3.leer(CLAVE_ULTIMO)["run_id"], s3.leer(CLAVE_LOCK)["estado"]) == (primera["run_id"], "free")


def test_corrida_posterior_a_una_caida_usa_run_y_tokens_nuevos(deps, athena, s3, reloj):
    correr(deps)
    reloj.avanzar(60)
    athena.programar_falla("tmp_a_hechos_07c", 2, veces=1)
    correr_fallida(deps)
    reloj.avanzar(60)
    tercera = correr(deps)
    primer_token = [i["token"] for i in athena.inicios if i["token"].startswith(f"maghsa-carga-{tercera['run_id']}")]
    assert primer_token[0] == f"maghsa-carga-{tercera['run_id']}-00001"


def test_fallo_en_07c_no_publica_nada(deps, athena, s3):
    sembrar_ultimo(s3)
    athena.programar_falla("tmp_a_hechos_07c", 2, veces=1)
    correr_fallida(deps)
    assert alter_en_run(athena) == []


def test_g15_fallida_revierte_en_orden_inverso(deps, athena, s3, glue):
    sembrar_ultimo(s3)
    athena.programar_compuerta("g15_publicacion", {"ctrl": "1"})
    correr_fallida(deps)
    assert alters_de_rollback(athena) == [HECHOS] + list(reversed(FORWARD_11))


def test_g15_fallida_deja_las_ubicaciones_previas(deps, athena, s3, glue):
    sembrar_ultimo(s3)
    athena.programar_compuerta("g15_publicacion", {"ctrl": "1"})
    correr_fallida(deps)
    assert ubicaciones_glue(glue) == {t: v.rstrip("/") for t, v in LEGADO.items()}


def test_g15_fallida_registra_estado_rollback(deps, athena, s3, capsys):
    sembrar_ultimo(s3)
    athena.programar_compuerta("g15_publicacion", {"ctrl": "1"})
    correr_fallida(deps)
    assert registros(capsys, "corrida")[0]["estado"] == "rollback"


def test_g15_fallida_conserva_ultimo_run(deps, athena, s3):
    sembrar_ultimo(s3)
    athena.programar_compuerta("g15_publicacion", {"ctrl": "1"})
    correr_fallida(deps)
    assert s3.leer(CLAVE_ULTIMO)["run_id"] == PREVIO_INICIAL


def test_falla_en_5to_alter_revierte_las_iniciadas(deps, athena, s3, glue):
    sembrar_ultimo(s3)
    athena.programar_falla("puente_proveedor_categoria_producto " + ALTER_EN_RUN, 2, veces=1)
    error = correr_fallida(deps)
    iniciadas = FORWARD_11[:5]
    assert (error.codigo, alters_de_rollback(athena)) == ("SENTENCIA_FALLIDA", list(reversed(iniciadas)))


def test_falla_en_5to_alter_no_toca_las_no_iniciadas(deps, athena, s3, glue):
    sembrar_ultimo(s3)
    athena.programar_falla("puente_proveedor_categoria_producto " + ALTER_EN_RUN, 2, veces=1)
    correr_fallida(deps)
    no_iniciadas = FORWARD_11[5:]
    assert not any(f"ALTER TABLE {t} {ALTER_EN_RUN}" in s for t in no_iniciadas for s in sentencias(athena))


def test_excepcion_no_carga_en_publicacion_revierte(deps, athena, s3, glue, monkeypatch):
    sembrar_ultimo(s3)
    ejecutar_original = athena_ejecutor.EjecutorAthena.ejecutar

    def ejecutar_con_fallo(self, sql, token, tope_s):
        if f"ALTER TABLE puente_proveedor_producto {ALTER_EN_RUN}" in sql:
            raise RuntimeError("fallo inesperado del cliente")
        return ejecutar_original(self, sql, token, tope_s)

    monkeypatch.setattr(athena_ejecutor.EjecutorAthena, "ejecutar", ejecutar_con_fallo)
    with pytest.raises(RuntimeError):
        correr(deps)
    assert ubicaciones_glue(glue) == {t: v.rstrip("/") for t, v in LEGADO.items()}


def test_rollback_fallido_no_reintenta_aunque_sea_reintentable(deps, athena, s3, capsys):
    sembrar_ultimo(s3)
    athena.programar_falla("dim_producto " + ALTER_EN_RUN, 1, veces=1)
    athena.programar_falla("SET LOCATION 's3://" + BUCKET + "/analytics/dim_", 2, veces=99)
    error = correr_fallida(deps)
    assert (error.codigo, len(ids_de_corrida(athena))) == ("SENTENCIA_FALLIDA", 1)


def test_rollback_fallido_marca_la_metrica(deps, athena, s3, capsys):
    sembrar_ultimo(s3)
    athena.programar_falla("dim_producto " + ALTER_EN_RUN, 1, veces=1)
    athena.programar_falla("SET LOCATION 's3://" + BUCKET + "/analytics/dim_", 2, veces=99)
    correr_fallida(deps)
    emf = [linea for linea in lineas(capsys) if "_aws" in linea][0]
    assert emf["RollbackFallido"] == 1


def test_modo_proyeccion_usa_14p(deps, athena, s3):
    sembrar_ultimo(s3)
    correr(deps)
    assert not any("DROP TABLE IF EXISTS hechos_compras" in s for s in sentencias(athena))


@pytest.mark.parametrize("parametros", [{}, {"projection.enabled": "false"}, {"projection.enabled": "TRUE"}])
def test_modo_recreate_usa_14r(deps, athena, glue, s3, parametros):
    glue.tablas[HECHOS]["Parameters"] = parametros
    sembrar_ultimo(s3)
    correr(deps)
    assert any(s.startswith(f"DROP TABLE IF EXISTS {HECHOS}") for s in sentencias(athena))


def test_modo_recreate_queda_registrado_en_ultimo_run(deps, glue, s3):
    glue.tablas[HECHOS]["Parameters"] = {}
    sembrar_ultimo(s3)
    correr(deps)
    assert s3.leer(CLAVE_ULTIMO)["hechos_modo"] == "recreate"


def test_modo_recreate_rollback_recrea_hechos_con_la_ubicacion_previa(deps, athena, glue, s3):
    glue.tablas[HECHOS]["Parameters"] = {}
    sembrar_ultimo(s3)
    athena.programar_compuerta("g15_publicacion", {"ctrl": "1"})
    correr_fallida(deps)
    assert glue.ubicacion(HECHOS).rstrip("/") == LEGADO[HECHOS].rstrip("/")


def test_ubicacion_previa_invalida_no_escribe_previos(deps, athena, glue, s3):
    glue.tablas["dim_proveedor"]["Location"] = "s3://otro-bucket/analytics/dim_proveedor/"
    sembrar_ultimo(s3)
    error = correr_fallida(deps)
    assert (error.codigo, s3.claves(PREFIJO_PREVIOS), alter_en_run(athena)) == (
        "UBICACION_PREVIA_INVALIDA", set(), [],
    )


def test_menos_de_90_s_no_publica(deps, athena, s3, glue):
    sembrar_ultimo(s3)
    athena.programar_costo("g3_nuevo", 760)
    error = correr_fallida(deps)
    assert (error.codigo, alter_en_run(athena), s3.claves(PREFIJO_PREVIOS)) == (
        "PRESUPUESTO_AGOTADO", [], set(),
    )


def test_verificacion_glue_detecta_set_location_ignorado(deps, athena, s3, glue):
    sembrar_ultimo(s3)
    athena.ignorar_efecto("dim_producto " + ALTER_EN_RUN)
    error = correr_fallida(deps)
    assert (error.codigo, ubicaciones_glue(glue)) == (
        "PUBLICACION_FALLIDA", {t: v.rstrip("/") for t, v in LEGADO.items()},
    )


def test_fallo_en_99_no_invalida_la_corrida(deps, athena, s3):
    sembrar_ultimo(s3)
    athena.programar_falla("DROP VIEW IF EXISTS tmp_v_compras", 2, veces=1)
    assert correr(deps)["estado"] == "ok"


# --- Logs y EMF -------------------------------------------------------------------------

def test_emf_namespace_y_dimensiones(deps, s3, capsys):
    sembrar_ultimo(s3)
    correr(deps)
    definicion = next(linea for linea in lineas(capsys) if "_aws" in linea)["_aws"]["CloudWatchMetrics"][0]
    assert (definicion["Namespace"], definicion["Dimensions"]) == ("MAGHSA/CargaDWH", [[]])


def test_emf_run_ok_uno_en_corrida_correcta(deps, s3, capsys):
    sembrar_ultimo(s3)
    correr(deps)
    emf = next(linea for linea in lineas(capsys) if "_aws" in linea)
    assert emf["RunOK"] == 1


def test_emf_timestamp_es_entero(deps, s3, capsys):
    sembrar_ultimo(s3)
    correr(deps)
    emf = next(linea for linea in lineas(capsys) if "_aws" in linea)
    assert isinstance(emf["_aws"]["Timestamp"], int)


def test_log_corrida_registra_estado_y_run(deps, s3, capsys):
    sembrar_ultimo(s3)
    correr(deps)
    corrida = registros(capsys, "corrida")[0]
    assert (corrida["run_id"], corrida["estado"]) == (RUN_BASE, "ok")
