import base64
import hmac
import json

import pytest

CODIGO = "codigo-de-prueba"

VALIDOS = {
    "productos": {"nombre": "Bujia", "categoria_id": "CAT01", "unidad_medida": "unidad", "descripcion": "x"},
    "categorias": {"nombre_categoria": "Neumaticos", "familia_gasto": "Mantenimiento"},
    "categorias_proveedor": {"nombre": "Servicios", "descripcion": ""},
    "unidades_organizacionales": {"nombre": "Logistica"},
    "proveedores": {
        "nombre": "Gamma", "pais": "Guatemala", "localizacion": "", "condiciones_pago": "30 días",
        "estado": "vigente", "categorias_proveedor_ids": ["CATPROV01"], "categorias_producto_ids": ["CAT01"],
        "producto_ids": ["PROD001"], "telefonos": "+502 5555-1234",
    },
    "compras": {
        "fecha": "2026-11-03", "proveedor_id": "PRV001", "producto_id": "PROD001", "categoria_id": "CAT01",
        "unidad_organizacional_id": "UO01", "cantidad": "2", "precio_unitario": "10.5",
        "condicion_pago": "30 días", "lead_time_dias": "4",
    },
}


def invocar(lf, evento):
    respuesta = lf.lambda_handler(evento, None)
    return respuesta["statusCode"], json.loads(respuesta["body"])


def evento(**campos):
    return {"body": json.dumps({"codigo_acceso": CODIGO, **campos})}


def pedir(lf, entidad, accion, datos=None):
    return invocar(lf, evento(entidad=entidad, accion=accion, datos=datos or {}))


def registros(lf, entidad):
    return pedir(lf, entidad, "listar")[1]["registros"]


def guardar_compra(lf, accion, **campos):
    if accion == "crear":
        return pedir(lf, "compras", "crear", {**VALIDOS["compras"], **campos})
    return pedir(lf, "compras", "actualizar", {"id_compra": "OCW0001", **campos})


def compra_guardada(lf, accion, respuesta):
    if accion == "crear":
        return respuesta[1]["registro"]
    return next(r for r in registros(lf, "compras") if r["id_compra"] == "OCW0001")


EXITO = {"crear": 201, "actualizar": 200}


# --- Punto 1: entradas mal formadas -> 400, nunca 500 ---

@pytest.mark.parametrize("cuerpo", ["[]", "5", "null", '"texto"', "{no json", "[" * 100_000, "x" * 100_001])
def test_cuerpo_mal_formado_devuelve_400(lf, cuerpo):
    estado, cuerpo_respuesta = invocar(lf, {"body": cuerpo})
    assert estado == 400
    assert cuerpo_respuesta["errores"]


def test_cuerpo_base64_valido_se_decodifica(lf):
    crudo = json.dumps({"codigo_acceso": CODIGO, "entidad": "categorias", "accion": "listar"}).encode()
    estado, _ = invocar(lf, {"body": base64.b64encode(crudo).decode(), "isBase64Encoded": True})
    assert estado == 200


@pytest.mark.parametrize("cuerpo", ["***no-base64***", base64.b64encode(b"\xff\xfe").decode()])
def test_cuerpo_base64_invalido_devuelve_400(lf, cuerpo):
    assert invocar(lf, {"body": cuerpo, "isBase64Encoded": True})[0] == 400


@pytest.mark.parametrize("sobre", [{}, {"body": None}, {"body": ""}])
def test_sin_cuerpo_devuelve_403(lf, sobre):
    assert invocar(lf, sobre)[0] == 403


def test_evento_que_no_es_objeto_devuelve_403(lf):
    assert lf.lambda_handler(None, None)["statusCode"] == 403


def test_options_devuelve_200(lf):
    assert invocar(lf, {"requestContext": {"http": {"method": "OPTIONS"}}})[0] == 200


@pytest.mark.parametrize("valor", [[], {}, 5, None, True])
def test_entidad_que_no_es_texto_devuelve_400(lf, valor):
    assert invocar(lf, evento(entidad=valor, accion="listar"))[0] == 400


@pytest.mark.parametrize("valor", [[], {}, 5, None, True])
def test_accion_que_no_es_texto_devuelve_400(lf, valor):
    assert invocar(lf, evento(entidad="categorias", accion=valor))[0] == 400


@pytest.mark.parametrize("accion", ["crear", "actualizar", "eliminar"])
@pytest.mark.parametrize("datos", [None, [], 5, "x", True])
def test_datos_que_no_es_objeto_devuelve_400(lf, accion, datos):
    for entidad in VALIDOS:
        assert invocar(lf, evento(entidad=entidad, accion=accion, datos=datos))[0] == 400


@pytest.mark.parametrize("campo", ["proveedor_id", "producto_id", "fecha", "lead_time_dias", "cantidad", "condicion_pago"])
@pytest.mark.parametrize("valor", [[], {}, [1], {"a": 1}])
@pytest.mark.parametrize("accion", ["crear", "actualizar"])
def test_compra_con_lista_o_dict_devuelve_400(lf, accion, campo, valor):
    assert guardar_compra(lf, accion, **{campo: valor})[0] == 400


def test_id_que_no_es_texto_devuelve_400(lf):
    for entidad, campo in (("productos", "producto_id"), ("compras", "id_compra"), ("proveedores", "proveedor_id")):
        for accion in ("actualizar", "eliminar"):
            assert pedir(lf, entidad, accion, {campo: ["x"]})[0] == 400


def test_error_inesperado_devuelve_500_generico_y_se_registra(lf, monkeypatch, caplog):
    def falla(_entidad):
        raise RuntimeError("fallo en s3://bucket-de-prueba/raw/secreto.csv")

    monkeypatch.setattr(lf, "_manejar_listar", falla)
    with caplog.at_level("ERROR"):
        estado, cuerpo = pedir(lf, "categorias", "listar")
    texto = json.dumps(cuerpo)
    assert estado == 500
    for detalle in ("bucket-de-prueba", "secreto", "Traceback", "RuntimeError"):
        assert detalle not in texto
    assert "secreto.csv" in caplog.text
    assert CODIGO not in caplog.text


# --- Punto 2: codigo de acceso ---

def test_codigo_correcto_devuelve_200(lf):
    assert pedir(lf, "categorias", "listar")[0] == 200


@pytest.mark.parametrize("codigo", ["otro", "", 123, [], {}, None, True, "\ud800"])
def test_codigo_incorrecto_o_no_texto_devuelve_403_generico(lf, codigo):
    cuerpo = json.dumps({"codigo_acceso": codigo, "entidad": "categorias", "accion": "listar"})
    estado, respuesta = invocar(lf, {"body": cuerpo})
    assert estado == 403
    assert respuesta == {"errores": ["Codigo de acceso invalido."]}


def test_codigo_se_compara_con_compare_digest_sobre_bytes(lf, monkeypatch):
    llamadas, real = [], hmac.compare_digest
    monkeypatch.setattr(lf.hmac, "compare_digest", lambda a, b: llamadas.append((a, b)) or real(a, b))
    pedir(lf, "categorias", "listar")
    assert llamadas and all(isinstance(a, bytes) and isinstance(b, bytes) for a, b in llamadas)


@pytest.mark.parametrize("codigo", ["", CODIGO])
def test_access_code_vacio_nunca_autentica(lf, monkeypatch, codigo):
    monkeypatch.setattr(lf, "ACCESS_CODE", "")
    cuerpo = json.dumps({"codigo_acceso": codigo, "entidad": "categorias", "accion": "listar"})
    assert invocar(lf, {"body": cuerpo})[0] == 401


# --- Punto 3: crear / actualizar / eliminar de las demas entidades ---

@pytest.mark.parametrize("entidad", list(VALIDOS))
def test_crear_valido_devuelve_201_y_persiste(lf, entidad):
    antes = len(registros(lf, entidad))
    estado, cuerpo = pedir(lf, entidad, "crear", VALIDOS[entidad])
    assert estado == 201
    assert len(registros(lf, entidad)) == antes + 1
    assert cuerpo["registro"]


def test_proveedor_normaliza_condicion_de_pago(lf):
    _, cuerpo = pedir(lf, "proveedores", "crear", VALIDOS["proveedores"])
    assert cuerpo["registro"]["condiciones_pago"] == "30 dias"


INVALIDOS = [
    ("productos", "nombre", ""), ("productos", "nombre", "   "), ("productos", "nombre", "x" * 101),
    ("productos", "nombre", "a\nb"), ("productos", "nombre", "a\x00b"), ("productos", "nombre", "=1+1"),
    ("productos", "nombre", "@cmd"), ("productos", "nombre", "-2+3"), ("productos", "nombre", "-Cable"),
    ("productos", "nombre", "\ud800"), ("proveedores", "nombre_contacto", "\ud800"),
    ("productos", "nombre", ["a"]),
    ("productos", "nombre", {"a": 1}), ("productos", "nombre", 5), ("productos", "unidad_medida", ""),
    ("productos", "categoria_id", "CAT99"), ("productos", "categoria_id", ["CAT01"]),
    ("categorias", "nombre_categoria", "repuestos"), ("categorias", "familia_gasto", ""),
    ("categorias_proveedor", "nombre", "Repuestos"),
    ("unidades_organizacionales", "nombre", "MANTENIMIENTO"),
    ("proveedores", "nombre", "\t"), ("proveedores", "estado", "otro"), ("proveedores", "estado", ["vigente"]),
    ("proveedores", "condiciones_pago", "tres meses"), ("proveedores", "condiciones_pago", ["30 dias"]),
    ("proveedores", "telefonos", "+SUM(A1)"), ("proveedores", "telefonos", "-5555"),
    ("proveedores", "correos", "a\r\nb"),
    ("proveedores", "categorias_proveedor_ids", []), ("proveedores", "categorias_proveedor_ids", "CATPROV01"),
    ("proveedores", "categorias_proveedor_ids", ["CATPROV99"]),
    ("proveedores", "categorias_producto_ids", ["CAT02"]), ("proveedores", "producto_ids", [["PROD001"]]),
]


@pytest.mark.parametrize("entidad,campo,valor", INVALIDOS)
def test_crear_invalido_devuelve_400_y_no_escribe(lf, entidad, campo, valor):
    antes = registros(lf, entidad)
    estado, cuerpo = pedir(lf, entidad, "crear", {**VALIDOS[entidad], campo: valor})
    assert estado == 400
    assert cuerpo["errores"]
    assert registros(lf, entidad) == antes


@pytest.mark.parametrize("entidad,campo,valor", [
    ("productos", "nombre", "Llanta agricola 18.4-30"), ("productos", "nombre", "Aceite de motor 15W-40"),
    ("proveedores", "nombre", "Aceros y Maquinaria S.A."), ("proveedores", "telefonos", "5512-3344"),
    ("proveedores", "condiciones_pago", "contado"), ("proveedores", "estado", "inactivo"),
    ("proveedores", "correos", "cmendez@repagronorte.com.gt"), ("categorias", "nombre_categoria", "Aceites y lubricantes"),
])
def test_valores_del_historico_son_validos(lf, entidad, campo, valor):
    assert pedir(lf, entidad, "crear", {**VALIDOS[entidad], campo: valor})[0] == 201


def test_actualizar_parcial_valido_conserva_el_resto(lf):
    assert pedir(lf, "productos", "actualizar", {"producto_id": "PROD001", "nombre": "Nuevo"})[0] == 200
    fila = next(r for r in registros(lf, "productos") if r["producto_id"] == "PROD001")
    assert (fila["nombre"], fila["categoria_id"]) == ("Nuevo", "CAT01")


@pytest.mark.parametrize("entidad,id_campo,id_valor,campo,valor", [
    ("productos", "producto_id", "PROD001", "nombre", ""),
    ("productos", "producto_id", "PROD001", "categoria_id", "CAT99"),
    ("categorias", "categoria_id", "CAT01", "nombre_categoria", "aceites"),
    ("unidades_organizacionales", "unidad_organizacional_id", "UO01", "nombre", "produccion"),
    ("categorias_proveedor", "categoria_proveedor_id", "CATPROV01", "nombre", "COMBUSTIBLES"),
    ("proveedores", "proveedor_id", "PRV001", "estado", "otro"),
    ("proveedores", "proveedor_id", "PRV001", "condiciones_pago", "pronto"),
])
def test_actualizar_invalido_devuelve_400_y_no_escribe(lf, entidad, id_campo, id_valor, campo, valor):
    antes = registros(lf, entidad)
    assert pedir(lf, entidad, "actualizar", {id_campo: id_valor, campo: valor})[0] == 400
    assert registros(lf, entidad) == antes


def test_actualizar_con_su_propio_nombre_no_es_duplicado(lf):
    assert pedir(lf, "categorias", "actualizar", {"categoria_id": "CAT01", "nombre_categoria": "REPUESTOS"})[0] == 200


def test_actualizar_proveedor_invalido_no_deja_escritura_parcial(lf):
    datos = {"proveedor_id": "PRV001", "nombre": "Nuevo", "categorias_proveedor_ids": ["CATPROV99"]}
    assert pedir(lf, "proveedores", "actualizar", datos)[0] == 400
    assert next(r for r in registros(lf, "proveedores") if r["proveedor_id"] == "PRV001")["nombre"] == "Alfa"


def test_actualizar_proveedor_valido_normaliza_y_reemplaza_relaciones(lf):
    datos = {"proveedor_id": "PRV001", "condiciones_pago": "60 Días", "categorias_proveedor_ids": ["CATPROV01"],
             "categorias_producto_ids": ["CAT01"], "producto_ids": ["PROD003"]}
    assert pedir(lf, "proveedores", "actualizar", datos)[0] == 200
    assert next(r for r in registros(lf, "proveedores") if r["proveedor_id"] == "PRV001")["condiciones_pago"] == "60 dias"
    pares = [(r["proveedor_id"], r["producto_id"]) for r in registros(lf, "proveedor_x_producto")]
    assert ("PRV001", "PROD003") in pares and ("PRV001", "PROD001") not in pares


@pytest.mark.parametrize("entidad,id_campo", [("productos", "producto_id"), ("compras", "id_compra")])
def test_actualizar_id_inexistente_devuelve_404(lf, entidad, id_campo):
    assert pedir(lf, entidad, "actualizar", {id_campo: "NOPE"})[0] == 404


EN_USO = [
    ("productos", "PROD001"), ("productos", "PROD002"), ("proveedores", "PRV001"), ("proveedores", "PRV002"),
    ("categorias", "CAT01"), ("categorias_proveedor", "CATPROV01"),
    ("unidades_organizacionales", "UO01"), ("unidades_organizacionales", "UO02"),
]
LIBRES = [
    ("productos", "PROD003"), ("proveedores", "PRV003"), ("categorias", "CAT03"),
    ("categorias_proveedor", "CATPROV03"), ("unidades_organizacionales", "UO03"), ("compras", "OCW0001"),
]


def ids(lf, entidad):
    return {r[lf.PREFIJOS_ID[entidad]] for r in registros(lf, entidad)}


@pytest.mark.parametrize("entidad,id_valor", EN_USO)
def test_eliminar_referenciado_devuelve_409_y_no_borra(lf, entidad, id_valor):
    estado, cuerpo = pedir(lf, entidad, "eliminar", {lf.PREFIJOS_ID[entidad]: id_valor})
    assert estado == 409
    assert id_valor in cuerpo["errores"][0]
    assert id_valor in ids(lf, entidad)


@pytest.mark.parametrize("entidad,id_valor", LIBRES)
def test_eliminar_sin_referencias_borra(lf, entidad, id_valor):
    assert pedir(lf, entidad, "eliminar", {lf.PREFIJOS_ID[entidad]: id_valor})[0] == 200
    assert id_valor not in ids(lf, entidad)


def test_eliminar_inexistente_devuelve_404_y_sin_id_devuelve_400(lf):
    assert pedir(lf, "productos", "eliminar", {"producto_id": "NOPE"})[0] == 404
    assert pedir(lf, "productos", "eliminar", {})[0] == 400


def test_eliminar_con_listado_fallido_devuelve_500_y_no_borra(lf):
    lf.s3.fallar_listado = True
    assert pedir(lf, "productos", "eliminar", {"producto_id": "PROD003"})[0] == 500
    assert "PROD003" in ids(lf, "productos")


# --- Compras (casos de t3b_verify.py) ---

@pytest.mark.parametrize("accion", ["crear", "actualizar"])
@pytest.mark.parametrize("lead", ["", "-1", "2.5", "abc", "5_0", " 5", "+5", "99999", None, True, 2.5])
def test_lead_time_invalido_devuelve_400(lf, accion, lead):
    assert guardar_compra(lf, accion, lead_time_dias=lead)[0] == 400


@pytest.mark.parametrize("accion", ["crear", "actualizar"])
@pytest.mark.parametrize("lead", ["0", 15, "9999"])
def test_lead_time_valido(lf, accion, lead):
    assert guardar_compra(lf, accion, lead_time_dias=lead)[0] == EXITO[accion]


@pytest.mark.parametrize("accion", ["crear", "actualizar"])
@pytest.mark.parametrize("fecha", ["", "2026-13-01", "2026-02-30", "05/01/2026", "no", None, "2026-11-04"])
def test_fecha_invalida_o_futura_devuelve_400(lf, accion, fecha):
    assert guardar_compra(lf, accion, fecha=fecha)[0] == 400


@pytest.mark.parametrize("accion", ["crear", "actualizar"])
@pytest.mark.parametrize("fecha", ["2026-11-03", "1990-01-01"])
def test_fecha_de_hoy_en_guatemala_o_pasada_es_valida(lf, accion, fecha):
    assert guardar_compra(lf, accion, fecha=fecha)[0] == EXITO[accion]


@pytest.mark.parametrize("accion", ["crear", "actualizar"])
def test_fecha_se_guarda_normalizada(lf, accion):
    respuesta = guardar_compra(lf, accion, fecha="2026-1-5")
    assert compra_guardada(lf, accion, respuesta)["fecha"] == "2026-01-05"


@pytest.mark.parametrize("accion", ["crear", "actualizar"])
@pytest.mark.parametrize("campo", ["cantidad", "precio_unitario"])
@pytest.mark.parametrize("valor", ["nan", "inf", "-inf", "NaN", "Infinity", "1e999", "1e3", "1_0", "0", "-2", "",
                                   "1" * 20, True, None, float("nan"), float("inf")])
def test_numero_no_finito_o_no_positivo_devuelve_400(lf, accion, campo, valor):
    assert guardar_compra(lf, accion, **{campo: valor})[0] == 400


@pytest.mark.parametrize("accion", ["crear", "actualizar"])
@pytest.mark.parametrize("campo,valor", [
    ("categoria_id", "CAT99"), ("moneda", "USD"), ("moneda", ""), ("moneda", ["GTQ"]),
    ("condicion_pago", ""), ("condicion_pago", "pronto"), ("condicion_pago", ["30 dias"]),
    ("unidad_organizacional_id", "ZZ"), ("proveedor_id", "PX"),
])
def test_referencia_o_valor_permitido_invalido_devuelve_400(lf, accion, campo, valor):
    assert guardar_compra(lf, accion, **{campo: valor})[0] == 400


def test_crear_compra_sin_moneda_usa_gtq_y_normaliza_condicion(lf):
    _, cuerpo = guardar_compra(lf, "crear")
    assert (cuerpo["registro"]["moneda"], cuerpo["registro"]["condicion_pago"]) == ("GTQ", "30 dias")


def test_crear_compra_sin_lead_time_devuelve_400(lf):
    datos = {k: v for k, v in VALIDOS["compras"].items() if k != "lead_time_dias"}
    assert pedir(lf, "compras", "crear", datos)[0] == 400


def test_compra_con_producto_ajeno_al_proveedor_devuelve_400(lf):
    assert guardar_compra(lf, "crear", producto_id="PROD002")[0] == 400
    assert guardar_compra(lf, "actualizar", producto_id="PROD002")[0] == 400
    assert guardar_compra(lf, "actualizar", proveedor_id="PRV002")[0] == 400


def test_actualizar_compra_con_par_proveedor_producto_coherente(lf):
    assert guardar_compra(lf, "actualizar", proveedor_id="PRV002", producto_id="PROD002", categoria_id="CAT02")[0] == 200


def test_actualizar_compra_parcial_conserva_el_resto(lf):
    assert guardar_compra(lf, "actualizar", lead_time_dias="7")[0] == 200
    fila = compra_guardada(lf, "actualizar", None)
    assert (fila["lead_time_dias"], fila["cantidad"]) == ("7", "2")


def test_actualizar_compra_invalida_no_escribe(lf):
    assert guardar_compra(lf, "actualizar", lead_time_dias="-1")[0] == 400
    assert compra_guardada(lf, "actualizar", None)["lead_time_dias"] == "5"


def test_actualizar_compra_legacy_con_lead_time_vacio_exige_corregirlo(lf):
    fila = {c: "" for c in lf.COLUMNAS["compras"]}
    fila.update(id_compra="OCW0001", fecha="2026-10-01", proveedor_id="PRV001", producto_id="PROD001",
                categoria_id="CAT01", unidad_organizacional_id="UO01", cantidad="2", precio_unitario="10",
                moneda="GTQ", condicion_pago="30 dias")
    lf._escribir_csv(lf.RUTAS["compras"], lf.COLUMNAS["compras"], [fila])
    assert guardar_compra(lf, "actualizar", cantidad="3")[0] == 400
