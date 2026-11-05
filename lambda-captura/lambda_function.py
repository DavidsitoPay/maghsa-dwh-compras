"""
Modulo de captura y mantenimiento de datos de compras (MAGHSA, S.A.) - v2

Incorpora el modelo normalizado proveedor <-> categoria_proveedor <->
categoria_producto <-> producto (relaciones N:M), y unidad_organizacional
como catalogo propio en vez de texto libre.

Variables de entorno requeridas:
    BUCKET_NAME   -> nombre del bucket S3 (zona raw/)
    ACCESS_CODE   -> codigo de acceso compartido para esta fase de pruebas

Ver README.md de este mismo modulo para el detalle de que cambiar al pasar
a la cuenta empresarial (Cognito en vez de ACCESS_CODE, nombre de bucket).
"""

import base64
import csv
import hmac
import io
import json
import logging
import os
import re
import unicodedata
from datetime import datetime, timedelta, timezone

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client("s3")

BUCKET_NAME = os.environ["BUCKET_NAME"]
ACCESS_CODE = os.environ.get("ACCESS_CODE", "")

# --- Maestros y catalogos con CRUD generico (una sola clave primaria) ---
RUTAS = {
    "proveedores": "raw/proveedores/maestro_proveedores.csv",
    "productos": "raw/productos/maestro_productos.csv",
    "categorias": "raw/categorias/catalogo_categorias.csv",
    "categorias_proveedor": "raw/categorias_proveedor/categorias_proveedor.csv",
    "unidades_organizacionales": "raw/unidades_organizacionales/unidades_organizacionales.csv",
    "compras": "raw/compras_web/registro_compras_web.csv",
}

COLUMNAS = {
    "proveedores": ["proveedor_id", "nombre", "pais", "localizacion", "condiciones_pago", "estado"],
    "productos": ["producto_id", "nombre", "categoria_id", "unidad_medida", "descripcion"],
    "categorias": ["categoria_id", "nombre_categoria", "familia_gasto"],
    "categorias_proveedor": ["categoria_proveedor_id", "nombre", "descripcion"],
    "unidades_organizacionales": ["unidad_organizacional_id", "nombre"],
    "compras": [
        "id_compra", "fecha", "proveedor_id", "producto_id", "categoria_id",
        "unidad_organizacional_id", "cantidad", "precio_unitario", "moneda",
        "condicion_pago", "lead_time_dias",
    ],
}

PREFIJOS_ID = {
    "proveedores": "proveedor_id",
    "productos": "producto_id",
    "categorias": "categoria_id",
    "categorias_proveedor": "categoria_proveedor_id",
    "unidades_organizacionales": "unidad_organizacional_id",
    "compras": "id_compra",
}

# --- Tablas puente / regla de negocio: no tienen una sola clave primaria,
# se manejan aparte (ver _manejar_crear_proveedor / _manejar_actualizar_proveedor) ---
RUTA_PROVEEDOR_CATEGORIA_PROVEEDOR = "raw/proveedor_categoria_proveedor/proveedor_categoria_proveedor.csv"
RUTA_CATEGORIA_PROVEEDOR_X_CATEGORIA_PRODUCTO = (
    "raw/categoria_proveedor_x_categoria_producto/categoria_proveedor_x_categoria_producto.csv"
)
RUTA_PROVEEDOR_CATEGORIA_PRODUCTO = "raw/proveedor_categoria_producto/proveedor_categoria_producto.csv"
RUTA_PROVEEDOR_X_PRODUCTO = "raw/proveedor_x_producto/proveedor_x_producto.csv"
RUTA_CONTACTO_PROVEEDOR = "raw/contacto_proveedor/contacto_proveedor.csv"

COLUMNAS_PROVEEDOR_CATEGORIA_PROVEEDOR = ["proveedor_id", "categoria_proveedor_id"]
COLUMNAS_CATEGORIA_PROVEEDOR_X_CATEGORIA_PRODUCTO = ["categoria_proveedor_id", "categoria_id"]
COLUMNAS_PROVEEDOR_CATEGORIA_PRODUCTO = ["proveedor_id", "categoria_id"]
COLUMNAS_PROVEEDOR_X_PRODUCTO = ["proveedor_id", "producto_id"]
COLUMNAS_CONTACTO_PROVEEDOR = ["proveedor_id", "nombre_contacto", "telefonos", "correos"]

# Entidades de solo lectura (alimentan los checkboxes/dropdowns del formulario)
RUTAS_LECTURA = {
    "proveedor_categoria_proveedor": RUTA_PROVEEDOR_CATEGORIA_PROVEEDOR,
    "categoria_proveedor_x_categoria_producto": RUTA_CATEGORIA_PROVEEDOR_X_CATEGORIA_PRODUCTO,
    "proveedor_categoria_producto": RUTA_PROVEEDOR_CATEGORIA_PRODUCTO,
    "proveedor_x_producto": RUTA_PROVEEDOR_X_PRODUCTO,
    "contacto_proveedor": RUTA_CONTACTO_PROVEEDOR,
}

FORMATO_ID = {
    "proveedores": ("PRV", 3), "productos": ("PROD", 3), "categorias": ("CAT", 2),
    "categorias_proveedor": ("CATPROV", 2), "unidades_organizacionales": ("UO", 2),
    "compras": ("OCW", 4),
}

MAX_CUERPO_CARACTERES = 100_000
MONEDAS = ("GTQ",)
ESTADOS_PROVEEDOR = ("vigente", "inactivo")
CONDICION_PAGO = re.compile(r"contado|[0-9]{1,3} dias")
MSG_CONDICION_PAGO = "La condicion de pago debe ser 'contado' o 'N dias' (por ejemplo, 30 dias)."
INICIO_FORMULA = re.compile(r"[=@+\-]")
TELEFONO = re.compile(r"\+?[0-9][0-9 ()\-,/]*")
CAMPOS_LISTA_PROVEEDOR = ("categorias_proveedor_ids", "categorias_producto_ids", "producto_ids")
CAMPOS_CONTACTO = ("nombre_contacto", "telefonos", "correos")

# campo: (longitud maxima, obligatorio)
CAMPOS_TEXTO = {
    "proveedores": {
        "nombre": (100, True), "pais": (60, True), "localizacion": (100, False),
        "nombre_contacto": (100, False), "telefonos": (60, False), "correos": (150, False),
    },
    "productos": {"nombre": (100, True), "unidad_medida": (30, True), "descripcion": (200, False)},
    "categorias": {"nombre_categoria": (100, True), "familia_gasto": (50, True)},
    "categorias_proveedor": {"nombre": (100, True), "descripcion": (200, False)},
    "unidades_organizacionales": {"nombre": (100, True)},
}
NOMBRE_UNICO = {
    "categorias": "nombre_categoria", "categorias_proveedor": "nombre", "unidades_organizacionales": "nombre",
}

TODAS_LAS_COMPRAS = "<todas las compras>"
# la columna referenciada se llama igual que la clave de la entidad
REFERENCIAS = {
    "proveedores": [(TODAS_LAS_COMPRAS, "compras")],
    "productos": [(TODAS_LAS_COMPRAS, "compras"), (RUTA_PROVEEDOR_X_PRODUCTO, "relaciones proveedor-producto")],
    "categorias": [
        (RUTAS["productos"], "productos"),
        (TODAS_LAS_COMPRAS, "compras"),
        (RUTA_PROVEEDOR_CATEGORIA_PRODUCTO, "categorias de producto de proveedores"),
        (RUTA_CATEGORIA_PROVEEDOR_X_CATEGORIA_PRODUCTO, "reglas de categoria de proveedor"),
    ],
    "categorias_proveedor": [
        (RUTA_PROVEEDOR_CATEGORIA_PROVEEDOR, "proveedores"),
        (RUTA_CATEGORIA_PROVEEDOR_X_CATEGORIA_PRODUCTO, "reglas de categoria de proveedor"),
    ],
    "unidades_organizacionales": [(TODAS_LAS_COMPRAS, "compras")],
    "compras": [],
}


def _respuesta(status_code, cuerpo):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(cuerpo, ensure_ascii=False),
    }


def _leer_csv(ruta):
    try:
        obj = s3.get_object(Bucket=BUCKET_NAME, Key=ruta)
        contenido = obj["Body"].read().decode("utf-8")
        return list(csv.DictReader(io.StringIO(contenido)))
    except s3.exceptions.NoSuchKey:
        return []


def _escribir_csv(ruta, columnas, filas):
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columnas)
    writer.writeheader()
    writer.writerows(filas)
    s3.put_object(Bucket=BUCKET_NAME, Key=ruta, Body=buffer.getvalue().encode("utf-8"))


def _siguiente_id(filas, campo_id, prefijo, ancho):
    numeros = []
    for fila in filas:
        valor = fila.get(campo_id, "")
        digitos = "".join(c for c in valor if c.isdigit())
        if digitos:
            numeros.append(int(digitos))
    siguiente = (max(numeros) + 1) if numeros else 1
    return f"{prefijo}{str(siguiente).zfill(ancho)}"


class SolicitudInvalida(Exception):
    pass


def _leer_cuerpo(event):
    crudo = event.get("body") or "{}"
    if not isinstance(crudo, str) or len(crudo) > MAX_CUERPO_CARACTERES:
        raise SolicitudInvalida("El cuerpo de la solicitud no es valido o es demasiado grande.")
    try:
        if event.get("isBase64Encoded"):
            crudo = base64.b64decode(crudo, validate=True).decode("utf-8")
        cuerpo = json.loads(crudo)
    except (ValueError, RecursionError):
        raise SolicitudInvalida("El cuerpo de la solicitud no es un JSON valido.") from None
    if not isinstance(cuerpo, dict):
        raise SolicitudInvalida("El cuerpo de la solicitud debe ser un objeto JSON.")
    return cuerpo


def _codigo_valido(codigo):
    if not isinstance(codigo, str):
        return False
    return hmac.compare_digest(
        codigo.encode("utf-8", "surrogatepass"), ACCESS_CODE.encode("utf-8", "surrogatepass")
    )


def _en(valor, coleccion):
    return isinstance(valor, str) and valor in coleccion


def _id_objetivo(datos, campo_id):
    valor = datos.get(campo_id)
    return valor.strip() if isinstance(valor, str) else ""


def _ids(entidad):
    return {fila[PREFIJOS_ID[entidad]] for fila in _leer_csv(RUTAS[entidad])}


def _condicion_pago(valor):
    if not isinstance(valor, str):
        return None
    ascii_minusculas = unicodedata.normalize("NFKD", valor).encode("ascii", "ignore").decode().lower()
    texto = " ".join(ascii_minusculas.split())
    return texto if CONDICION_PAGO.fullmatch(texto) else None


def _numero_positivo(valor):
    texto = str(valor)
    return re.fullmatch(r"[0-9]{1,15}(\.[0-9]{1,6})?", texto) is not None and float(texto) > 0


def _errores_texto(registro, campo, maximo, obligatorio):
    valor = registro.get(campo)
    if valor is None:
        valor = ""
    if not isinstance(valor, str):
        return [f"El campo '{campo}' debe ser texto."]
    valor = valor.strip()
    if not valor:
        return [f"El campo '{campo}' es obligatorio."] if obligatorio else []
    if len(valor) > maximo:
        return [f"El campo '{campo}' no puede superar {maximo} caracteres."]
    if any(unicodedata.category(c) in ("Cc", "Cs", "Zl", "Zp") for c in valor):
        return [f"El campo '{campo}' no puede contener saltos de linea ni caracteres de control."]
    if INICIO_FORMULA.match(valor) and not (campo == "telefonos" and TELEFONO.fullmatch(valor)):
        return [f"El campo '{campo}' no puede iniciar con =, +, - o @."]
    return []


def _limpiar(entidad, registro):
    return {c: registro[c].strip() for c in CAMPOS_TEXTO.get(entidad, {}) if isinstance(registro.get(c), str)}


def _errores_registro(entidad, registro, filas):
    errores = []
    for campo, (maximo, obligatorio) in CAMPOS_TEXTO[entidad].items():
        errores += _errores_texto(registro, campo, maximo, obligatorio)

    if entidad == "proveedores":
        if not _en(registro.get("estado"), ESTADOS_PROVEEDOR):
            errores.append("El estado debe ser vigente o inactivo.")
        if _condicion_pago(registro.get("condiciones_pago")) is None:
            errores.append(MSG_CONDICION_PAGO)
    elif entidad == "productos":
        if not _en(registro.get("categoria_id"), _ids("categorias")):
            errores.append("La categoria seleccionada no existe en el catalogo de categorias.")

    campo = NOMBRE_UNICO.get(entidad)
    nombre = registro.get(campo)
    if isinstance(nombre, str) and any(
        f.get(campo, "").strip().casefold() == nombre.strip().casefold()
        and f.get(PREFIJOS_ID[entidad]) != registro.get(PREFIJOS_ID[entidad])
        for f in filas
    ):
        errores.append(f"Ya existe un registro con ese valor en '{campo}'.")
    return errores


def _leer_listas_ids(datos):
    listas, errores = {}, []
    for campo in CAMPOS_LISTA_PROVEEDOR:
        valor = datos.get(campo) or []
        if not isinstance(valor, list) or not all(isinstance(v, str) for v in valor):
            errores.append(f"El campo {campo} debe ser una lista de identificadores.")
        else:
            listas[campo] = list(dict.fromkeys(valor))
    return listas, errores


def _rutas_compras():
    rutas = [RUTAS["compras"]]
    for pagina in s3.get_paginator("list_objects_v2").paginate(Bucket=BUCKET_NAME, Prefix="raw/compras/"):
        rutas += [o["Key"] for o in pagina.get("Contents", []) if o["Key"].endswith(".csv")]
    return rutas


def _valores_columna(origen, columna):
    rutas = _rutas_compras() if origen == TODAS_LAS_COMPRAS else [origen]
    return {fila.get(columna) for ruta in rutas for fila in _leer_csv(ruta)}


def _usos_de(entidad, id_objetivo):
    columna = PREFIJOS_ID[entidad]
    return [d for origen, d in REFERENCIAS[entidad] if id_objetivo in _valores_columna(origen, columna)]


# ---------------------------------------------------------------
# CRUD generico (proveedores base, productos, categorias,
# categorias_proveedor, unidades_organizacionales, compras)
# ---------------------------------------------------------------

# Guatemala no usa horario de verano; el offset fijo evita depender de tzdata en Lambda.
ZONA_GUATEMALA = timezone(timedelta(hours=-6))


def _hoy_guatemala():
    return datetime.now(ZONA_GUATEMALA).date()


def _fecha_compra(datos):
    return datetime.strptime(datos.get("fecha", ""), "%Y-%m-%d").date()


def _errores_fecha(datos):
    try:
        fecha = _fecha_compra(datos)
    except (TypeError, ValueError):
        return ["La fecha no tiene un formato valido (AAAA-MM-DD)."]
    if fecha > _hoy_guatemala():
        return ["La fecha no puede ser futura."]
    return []


def _errores_lead_time(datos):
    if not re.fullmatch(r"[0-9]{1,4}", str(datos.get("lead_time_dias", ""))):
        return ["El lead time (dias) es obligatorio y debe ser un numero entero entre 0 y 9999."]
    return []


def _leer_catalogos_compra():
    return {
        "proveedores": _ids("proveedores"),
        "productos": _ids("productos"),
        "categorias": _ids("categorias"),
        "unidades": _ids("unidades_organizacionales"),
        "pares": {(r["proveedor_id"], r["producto_id"]) for r in _leer_csv(RUTA_PROVEEDOR_X_PRODUCTO)},
    }


def _validar_compra(datos, catalogos):
    errores = []
    proveedor_id = datos.get("proveedor_id")
    producto_id = datos.get("producto_id")
    proveedor_existe = _en(proveedor_id, catalogos["proveedores"])
    producto_existe = _en(producto_id, catalogos["productos"])

    if not proveedor_existe:
        errores.append("El proveedor seleccionado no existe en el maestro de proveedores.")
    if not producto_existe:
        errores.append("El producto seleccionado no existe en el maestro de productos.")
    if proveedor_existe and producto_existe and (proveedor_id, producto_id) not in catalogos["pares"]:
        errores.append("Ese proveedor no tiene asociado ese producto.")
    if not _en(datos.get("unidad_organizacional_id"), catalogos["unidades"]):
        errores.append("La unidad organizacional seleccionada no existe en el catalogo.")
    if not _en(datos.get("categoria_id"), catalogos["categorias"]):
        errores.append("La categoria seleccionada no existe en el catalogo de categorias.")
    if not _numero_positivo(datos.get("cantidad")):
        errores.append("La cantidad debe ser un numero mayor a cero.")
    if not _numero_positivo(datos.get("precio_unitario")):
        errores.append("El precio unitario debe ser un numero mayor a cero.")
    if not _en(datos.get("moneda"), MONEDAS):
        errores.append("La moneda no es valida (solo GTQ).")
    if _condicion_pago(datos.get("condicion_pago")) is None:
        errores.append(MSG_CONDICION_PAGO)

    errores.extend(_errores_fecha(datos))
    errores.extend(_errores_lead_time(datos))
    return errores


def _manejar_listar(entidad):
    ruta = RUTAS[entidad] if entidad in RUTAS else RUTAS_LECTURA[entidad]
    filas = _leer_csv(ruta)
    return _respuesta(200, {"entidad": entidad, "registros": filas})


def _manejar_crear_generico(entidad, datos):
    filas = _leer_csv(RUTAS[entidad])
    campo_id = PREFIJOS_ID[entidad]
    prefijo, ancho = FORMATO_ID[entidad]
    datos = {**datos, campo_id: _siguiente_id(filas, campo_id, prefijo, ancho)}

    if entidad == "compras":
        datos.setdefault("moneda", "GTQ")
        errores = _validar_compra(datos, _leer_catalogos_compra())
    else:
        errores = _errores_registro(entidad, datos, filas)
    if errores:
        return _respuesta(400, {"errores": errores})

    if entidad == "compras":
        datos["fecha"] = _fecha_compra(datos).isoformat()
        datos["condicion_pago"] = _condicion_pago(datos["condicion_pago"])

    fila_nueva = {col: datos.get(col, "") for col in COLUMNAS[entidad]}
    filas.append(fila_nueva)
    _escribir_csv(RUTAS[entidad], COLUMNAS[entidad], filas)
    return _respuesta(201, {"mensaje": "Registro creado correctamente.", "registro": fila_nueva})


def _manejar_actualizar_generico(entidad, datos):
    campo_id = PREFIJOS_ID[entidad]
    id_objetivo = _id_objetivo(datos, campo_id)
    if not id_objetivo:
        return _respuesta(400, {"errores": [f"Falta el campo {campo_id} para identificar el registro."]})

    filas = _leer_csv(RUTAS[entidad])
    fila = next((f for f in filas if f.get(campo_id) == id_objetivo), None)
    if fila is None:
        return _respuesta(404, {"errores": ["No se encontro un registro con ese identificador."]})

    cambios = {col: datos[col] for col in COLUMNAS[entidad] if col in datos and col != campo_id}
    fusionado = {**fila, **cambios}
    if entidad == "compras":
        errores = _validar_compra(fusionado, _leer_catalogos_compra())
    else:
        errores = _errores_registro(entidad, fusionado, filas)
    if errores:
        return _respuesta(400, {"errores": errores})

    if "fecha" in cambios:
        cambios["fecha"] = _fecha_compra(cambios).isoformat()
    if "condicion_pago" in cambios:
        cambios["condicion_pago"] = _condicion_pago(cambios["condicion_pago"])
    fila.update(cambios)
    _escribir_csv(RUTAS[entidad], COLUMNAS[entidad], filas)
    return _respuesta(200, {"mensaje": "Registro actualizado correctamente."})


def _manejar_eliminar_generico(entidad, datos):
    campo_id = PREFIJOS_ID[entidad]
    id_objetivo = _id_objetivo(datos, campo_id)
    if not id_objetivo:
        return _respuesta(400, {"errores": [f"Falta el campo {campo_id} para identificar el registro."]})

    filas = _leer_csv(RUTAS[entidad])
    filas_restantes = [f for f in filas if f.get(campo_id) != id_objetivo]
    if len(filas_restantes) == len(filas):
        return _respuesta(404, {"errores": ["No se encontro un registro con ese identificador."]})

    usos = _usos_de(entidad, id_objetivo)
    if usos:
        return _respuesta(409, {"errores": [f"No se puede eliminar {id_objetivo}: esta en uso en {', '.join(usos)}."]})

    _escribir_csv(RUTAS[entidad], COLUMNAS[entidad], filas_restantes)
    if entidad == "proveedores":
        _eliminar_relaciones_proveedor(id_objetivo)
    return _respuesta(200, {"mensaje": "Registro eliminado correctamente."})


# ---------------------------------------------------------------
# Manejo especial de proveedor (base + relaciones N:M + contacto)
# ---------------------------------------------------------------

def _reemplazar_relaciones(ruta, columnas, proveedor_id, columna_relacionada, valores_nuevos):
    """Borra todas las filas de una tabla puente para un proveedor y escribe las nuevas."""
    filas = _leer_csv(ruta)
    filas = [f for f in filas if f.get("proveedor_id") != proveedor_id]
    for valor in valores_nuevos:
        filas.append({"proveedor_id": proveedor_id, columna_relacionada: valor})
    _escribir_csv(ruta, columnas, filas)


def _eliminar_relaciones_proveedor(proveedor_id):
    for ruta, columnas in [
        (RUTA_PROVEEDOR_CATEGORIA_PROVEEDOR, COLUMNAS_PROVEEDOR_CATEGORIA_PROVEEDOR),
        (RUTA_PROVEEDOR_CATEGORIA_PRODUCTO, COLUMNAS_PROVEEDOR_CATEGORIA_PRODUCTO),
        (RUTA_PROVEEDOR_X_PRODUCTO, COLUMNAS_PROVEEDOR_X_PRODUCTO),
    ]:
        filas = _leer_csv(ruta)
        filas = [f for f in filas if f.get("proveedor_id") != proveedor_id]
        _escribir_csv(ruta, columnas, filas)

    filas_contacto = _leer_csv(RUTA_CONTACTO_PROVEEDOR)
    filas_contacto = [f for f in filas_contacto if f.get("proveedor_id") != proveedor_id]
    _escribir_csv(RUTA_CONTACTO_PROVEEDOR, COLUMNAS_CONTACTO_PROVEEDOR, filas_contacto)


def _validar_asociaciones_proveedor(categorias_proveedor_ids, categorias_producto_ids, producto_ids):
    """Verifica que las categorias de producto y los productos elegidos sean compatibles
    con las categorias de proveedor marcadas, usando la tabla de reglas de negocio."""
    errores = []
    ids_categoria_proveedor = _ids("categorias_proveedor")
    for cat_id in categorias_proveedor_ids:
        if cat_id not in ids_categoria_proveedor:
            errores.append(f"La categoria de proveedor {cat_id} no existe en el catalogo.")

    reglas = _leer_csv(RUTA_CATEGORIA_PROVEEDOR_X_CATEGORIA_PRODUCTO)
    categorias_producto_permitidas = {
        r["categoria_id"] for r in reglas if r["categoria_proveedor_id"] in categorias_proveedor_ids
    }

    for cat_id in categorias_producto_ids:
        if cat_id not in categorias_producto_permitidas:
            errores.append(
                f"La categoria de producto {cat_id} no es valida para las categorias de "
                f"proveedor seleccionadas."
            )

    productos = _leer_csv(RUTAS["productos"])
    categoria_por_producto = {p["producto_id"]: p["categoria_id"] for p in productos}

    for prod_id in producto_ids:
        categoria_del_producto = categoria_por_producto.get(prod_id)
        if categoria_del_producto is None:
            errores.append(f"El producto {prod_id} no existe en el maestro de productos.")
        elif categoria_del_producto not in categorias_producto_ids:
            errores.append(
                f"El producto {prod_id} pertenece a una categoria que no fue marcada para "
                f"este proveedor."
            )

    return errores


def _manejar_crear_proveedor(datos):
    listas, errores = _leer_listas_ids(datos)
    if errores:
        return _respuesta(400, {"errores": errores})
    if not listas["categorias_proveedor_ids"]:
        return _respuesta(400, {"errores": ["Debe marcar al menos una categoria de proveedor."]})

    proveedores = _leer_csv(RUTAS["proveedores"])
    nuevo_id = _siguiente_id(proveedores, "proveedor_id", "PRV", 3)
    datos = {**datos, "proveedor_id": nuevo_id}
    errores = _errores_registro("proveedores", datos, proveedores) + _validar_asociaciones_proveedor(
        listas["categorias_proveedor_ids"], listas["categorias_producto_ids"], listas["producto_ids"]
    )
    if errores:
        return _respuesta(400, {"errores": errores})

    datos["condiciones_pago"] = _condicion_pago(datos["condiciones_pago"])
    fila_proveedor = {col: datos.get(col, "") for col in COLUMNAS["proveedores"]}
    proveedores.append(fila_proveedor)
    _escribir_csv(RUTAS["proveedores"], COLUMNAS["proveedores"], proveedores)

    _reemplazar_relaciones(
        RUTA_PROVEEDOR_CATEGORIA_PROVEEDOR, COLUMNAS_PROVEEDOR_CATEGORIA_PROVEEDOR,
        nuevo_id, "categoria_proveedor_id", listas["categorias_proveedor_ids"],
    )
    _reemplazar_relaciones(
        RUTA_PROVEEDOR_CATEGORIA_PRODUCTO, COLUMNAS_PROVEEDOR_CATEGORIA_PRODUCTO,
        nuevo_id, "categoria_id", listas["categorias_producto_ids"],
    )
    _reemplazar_relaciones(
        RUTA_PROVEEDOR_X_PRODUCTO, COLUMNAS_PROVEEDOR_X_PRODUCTO,
        nuevo_id, "producto_id", listas["producto_ids"],
    )

    if any(datos.get(c) for c in CAMPOS_CONTACTO):
        contactos = _leer_csv(RUTA_CONTACTO_PROVEEDOR)
        contactos.append({"proveedor_id": nuevo_id, **{c: datos.get(c, "") for c in CAMPOS_CONTACTO}})
        _escribir_csv(RUTA_CONTACTO_PROVEEDOR, COLUMNAS_CONTACTO_PROVEEDOR, contactos)

    return _respuesta(201, {"mensaje": "Proveedor creado correctamente.", "registro": fila_proveedor})


def _manejar_actualizar_proveedor(datos):
    proveedor_id = _id_objetivo(datos, "proveedor_id")
    if not proveedor_id:
        return _respuesta(400, {"errores": ["Falta el campo proveedor_id para identificar el registro."]})

    proveedores = _leer_csv(RUTAS["proveedores"])
    fila = next((f for f in proveedores if f.get("proveedor_id") == proveedor_id), None)
    if fila is None:
        return _respuesta(404, {"errores": ["No se encontro un proveedor con ese identificador."]})

    listas, errores = _leer_listas_ids(datos)
    cambios = {col: datos[col] for col in COLUMNAS["proveedores"] if col in datos and col != "proveedor_id"}
    contacto = {c: datos[c] for c in CAMPOS_CONTACTO if c in datos}
    actualiza_asociaciones = any(k in datos for k in CAMPOS_LISTA_PROVEEDOR)
    errores += _errores_registro("proveedores", {**fila, **cambios, **contacto}, proveedores)
    if actualiza_asociaciones and not errores:
        errores += _validar_asociaciones_proveedor(
            listas["categorias_proveedor_ids"], listas["categorias_producto_ids"], listas["producto_ids"]
        )
    if errores:
        return _respuesta(400, {"errores": errores})

    if "condiciones_pago" in cambios:
        cambios["condiciones_pago"] = _condicion_pago(cambios["condiciones_pago"])
    fila.update(cambios)
    _escribir_csv(RUTAS["proveedores"], COLUMNAS["proveedores"], proveedores)

    if actualiza_asociaciones:
        _reemplazar_relaciones(
            RUTA_PROVEEDOR_CATEGORIA_PROVEEDOR, COLUMNAS_PROVEEDOR_CATEGORIA_PROVEEDOR,
            proveedor_id, "categoria_proveedor_id", listas["categorias_proveedor_ids"],
        )
        _reemplazar_relaciones(
            RUTA_PROVEEDOR_CATEGORIA_PRODUCTO, COLUMNAS_PROVEEDOR_CATEGORIA_PRODUCTO,
            proveedor_id, "categoria_id", listas["categorias_producto_ids"],
        )
        _reemplazar_relaciones(
            RUTA_PROVEEDOR_X_PRODUCTO, COLUMNAS_PROVEEDOR_X_PRODUCTO,
            proveedor_id, "producto_id", listas["producto_ids"],
        )

    if contacto:
        contactos = [c for c in _leer_csv(RUTA_CONTACTO_PROVEEDOR) if c.get("proveedor_id") != proveedor_id]
        if any(contacto.values()):
            contactos.append({"proveedor_id": proveedor_id, **{c: contacto.get(c, "") for c in CAMPOS_CONTACTO}})
        _escribir_csv(RUTA_CONTACTO_PROVEEDOR, COLUMNAS_CONTACTO_PROVEEDOR, contactos)

    return _respuesta(200, {"mensaje": "Proveedor actualizado correctamente."})


def _procesar(event):
    if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return _respuesta(200, {})

    try:
        cuerpo = _leer_cuerpo(event)
    except SolicitudInvalida as error:
        return _respuesta(400, {"errores": [str(error)]})

    if not ACCESS_CODE:
        return _respuesta(401, {"errores": ["Acceso no configurado."]})
    if not _codigo_valido(cuerpo.get("codigo_acceso")):
        return _respuesta(403, {"errores": ["Codigo de acceso invalido."]})

    entidad = cuerpo.get("entidad")
    accion = cuerpo.get("accion")
    datos = cuerpo.get("datos", {})

    if not isinstance(entidad, str) or (entidad not in RUTAS and entidad not in RUTAS_LECTURA):
        return _respuesta(400, {"errores": ["Entidad no reconocida."]})

    if accion == "listar":
        return _manejar_listar(entidad)

    if entidad not in RUTAS:
        return _respuesta(400, {"errores": [f"La entidad '{entidad}' es de solo lectura."]})

    if not isinstance(datos, dict):
        return _respuesta(400, {"errores": ["El campo datos debe ser un objeto JSON."]})
    datos = {**datos, **_limpiar(entidad, datos)}

    if entidad == "proveedores":
        if accion == "crear":
            return _manejar_crear_proveedor(datos)
        if accion == "actualizar":
            return _manejar_actualizar_proveedor(datos)
        if accion == "eliminar":
            return _manejar_eliminar_generico(entidad, datos)
        return _respuesta(400, {"errores": ["Accion no reconocida."]})

    if accion == "crear":
        return _manejar_crear_generico(entidad, datos)
    if accion == "actualizar":
        return _manejar_actualizar_generico(entidad, datos)
    if accion == "eliminar":
        return _manejar_eliminar_generico(entidad, datos)

    return _respuesta(400, {"errores": ["Accion no reconocida."]})


def lambda_handler(event, context):
    try:
        return _procesar(event if isinstance(event, dict) else {})
    except Exception:
        logger.exception("Error inesperado procesando la solicitud")
        return _respuesta(500, {"errores": ["Error interno del servidor."]})
