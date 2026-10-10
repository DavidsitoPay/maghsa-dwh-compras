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

import csv
import io
import json
import os
from datetime import date, datetime

import boto3

s3 = boto3.client("s3")

BUCKET_NAME = os.environ["BUCKET_NAME"]
ACCESS_CODE = os.environ["ACCESS_CODE"]

# --- Maestros y catalogos con CRUD generico (una sola clave primaria) ---
RUTAS = {
    "proveedores": "raw/proveedores/maestro_proveedores.csv",
    "productos": "raw/productos/maestro_productos.csv",
    "categorias": "raw/categorias/catalogo_categorias.csv",
    "categorias_proveedor": "raw/categorias_proveedor/categorias_proveedor.csv",
    "unidades_organizacionales": "raw/unidades_organizacionales/unidades_organizacionales.csv",
    "compras": "raw/compras/anio=2026/mes=09/registro_compras_web.csv",
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


# ---------------------------------------------------------------
# CRUD generico (proveedores base, productos, categorias,
# categorias_proveedor, unidades_organizacionales, compras)
# ---------------------------------------------------------------

def _validar_compra(datos, proveedores, productos, proveedor_x_producto, unidades):
    errores = []

    ids_proveedor = {p["proveedor_id"] for p in proveedores}
    ids_producto = {p["producto_id"] for p in productos}
    ids_unidad = {u["unidad_organizacional_id"] for u in unidades}
    pares_proveedor_producto = {(r["proveedor_id"], r["producto_id"]) for r in proveedor_x_producto}

    proveedor_id = datos.get("proveedor_id")
    producto_id = datos.get("producto_id")

    if proveedor_id not in ids_proveedor:
        errores.append("El proveedor seleccionado no existe en el maestro de proveedores.")
    if producto_id not in ids_producto:
        errores.append("El producto seleccionado no existe en el maestro de productos.")
    if (
        proveedor_id in ids_proveedor
        and producto_id in ids_producto
        and (proveedor_id, producto_id) not in pares_proveedor_producto
    ):
        errores.append("Ese proveedor no tiene asociado ese producto.")
    if datos.get("unidad_organizacional_id") not in ids_unidad:
        errores.append("La unidad organizacional seleccionada no existe en el catalogo.")

    try:
        cantidad = float(datos.get("cantidad", 0))
        if cantidad <= 0:
            errores.append("La cantidad debe ser mayor a cero.")
    except (TypeError, ValueError):
        errores.append("La cantidad no es un numero valido.")

    try:
        precio = float(datos.get("precio_unitario", 0))
        if precio <= 0:
            errores.append("El precio unitario debe ser mayor a cero.")
    except (TypeError, ValueError):
        errores.append("El precio unitario no es un numero valido.")

    try:
        fecha = datetime.strptime(datos.get("fecha", ""), "%Y-%m-%d").date()
        if fecha > date.today():
            errores.append("La fecha no puede ser futura.")
    except ValueError:
        errores.append("La fecha no tiene un formato valido (AAAA-MM-DD).")

    return errores


def _manejar_listar(entidad):
    ruta = RUTAS[entidad] if entidad in RUTAS else RUTAS_LECTURA[entidad]
    filas = _leer_csv(ruta)
    return _respuesta(200, {"entidad": entidad, "registros": filas})


def _manejar_crear_generico(entidad, datos):
    filas = _leer_csv(RUTAS[entidad])

    if entidad == "compras":
        proveedores = _leer_csv(RUTAS["proveedores"])
        productos = _leer_csv(RUTAS["productos"])
        proveedor_x_producto = _leer_csv(RUTA_PROVEEDOR_X_PRODUCTO)
        unidades = _leer_csv(RUTAS["unidades_organizacionales"])
        errores = _validar_compra(datos, proveedores, productos, proveedor_x_producto, unidades)
        if errores:
            return _respuesta(400, {"errores": errores})
        nuevo_id = _siguiente_id(filas, "id_compra", "OC", 4)
        datos["id_compra"] = nuevo_id
        datos.setdefault("moneda", "GTQ")
    else:
        prefijos = {
            "proveedores": "PRV", "productos": "PROD", "categorias": "CAT",
            "categorias_proveedor": "CATPROV", "unidades_organizacionales": "UO",
        }
        anchos = {
            "proveedores": 3, "productos": 3, "categorias": 2,
            "categorias_proveedor": 2, "unidades_organizacionales": 2,
        }
        campo_id = PREFIJOS_ID[entidad]
        nuevo_id = _siguiente_id(filas, campo_id, prefijos[entidad], anchos[entidad])
        datos[campo_id] = nuevo_id

    fila_nueva = {col: datos.get(col, "") for col in COLUMNAS[entidad]}
    filas.append(fila_nueva)
    _escribir_csv(RUTAS[entidad], COLUMNAS[entidad], filas)
    return _respuesta(201, {"mensaje": "Registro creado correctamente.", "registro": fila_nueva})


def _manejar_actualizar_generico(entidad, datos):
    campo_id = PREFIJOS_ID[entidad]
    id_objetivo = datos.get(campo_id)
    if not id_objetivo:
        return _respuesta(400, {"errores": [f"Falta el campo {campo_id} para identificar el registro."]})

    filas = _leer_csv(RUTAS[entidad])
    encontrado = False
    for fila in filas:
        if fila.get(campo_id) == id_objetivo:
            for col in COLUMNAS[entidad]:
                if col in datos and col != campo_id:
                    fila[col] = datos[col]
            encontrado = True
            break

    if not encontrado:
        return _respuesta(404, {"errores": ["No se encontro un registro con ese identificador."]})

    _escribir_csv(RUTAS[entidad], COLUMNAS[entidad], filas)
    return _respuesta(200, {"mensaje": "Registro actualizado correctamente."})


def _manejar_eliminar_generico(entidad, datos):
    campo_id = PREFIJOS_ID[entidad]
    id_objetivo = datos.get(campo_id)
    if not id_objetivo:
        return _respuesta(400, {"errores": [f"Falta el campo {campo_id} para identificar el registro."]})

    filas = _leer_csv(RUTAS[entidad])
    filas_restantes = [f for f in filas if f.get(campo_id) != id_objetivo]

    if len(filas_restantes) == len(filas):
        return _respuesta(404, {"errores": ["No se encontro un registro con ese identificador."]})

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
    categorias_proveedor_ids = datos.get("categorias_proveedor_ids") or []
    categorias_producto_ids = datos.get("categorias_producto_ids") or []
    producto_ids = datos.get("producto_ids") or []

    if not categorias_proveedor_ids:
        return _respuesta(400, {"errores": ["Debe marcar al menos una categoria de proveedor."]})

    errores = _validar_asociaciones_proveedor(
        categorias_proveedor_ids, categorias_producto_ids, producto_ids
    )
    if errores:
        return _respuesta(400, {"errores": errores})

    proveedores = _leer_csv(RUTAS["proveedores"])
    nuevo_id = _siguiente_id(proveedores, "proveedor_id", "PRV", 3)

    fila_proveedor = {col: datos.get(col, "") for col in COLUMNAS["proveedores"]}
    fila_proveedor["proveedor_id"] = nuevo_id
    proveedores.append(fila_proveedor)
    _escribir_csv(RUTAS["proveedores"], COLUMNAS["proveedores"], proveedores)

    _reemplazar_relaciones(
        RUTA_PROVEEDOR_CATEGORIA_PROVEEDOR, COLUMNAS_PROVEEDOR_CATEGORIA_PROVEEDOR,
        nuevo_id, "categoria_proveedor_id", categorias_proveedor_ids,
    )
    _reemplazar_relaciones(
        RUTA_PROVEEDOR_CATEGORIA_PRODUCTO, COLUMNAS_PROVEEDOR_CATEGORIA_PRODUCTO,
        nuevo_id, "categoria_id", categorias_producto_ids,
    )
    _reemplazar_relaciones(
        RUTA_PROVEEDOR_X_PRODUCTO, COLUMNAS_PROVEEDOR_X_PRODUCTO,
        nuevo_id, "producto_id", producto_ids,
    )

    if datos.get("nombre_contacto") or datos.get("telefonos") or datos.get("correos"):
        contactos = _leer_csv(RUTA_CONTACTO_PROVEEDOR)
        contactos.append({
            "proveedor_id": nuevo_id,
            "nombre_contacto": datos.get("nombre_contacto", ""),
            "telefonos": datos.get("telefonos", ""),
            "correos": datos.get("correos", ""),
        })
        _escribir_csv(RUTA_CONTACTO_PROVEEDOR, COLUMNAS_CONTACTO_PROVEEDOR, contactos)

    return _respuesta(201, {"mensaje": "Proveedor creado correctamente.", "registro": fila_proveedor})


def _manejar_actualizar_proveedor(datos):
    proveedor_id = datos.get("proveedor_id")
    if not proveedor_id:
        return _respuesta(400, {"errores": ["Falta el campo proveedor_id para identificar el registro."]})

    proveedores = _leer_csv(RUTAS["proveedores"])
    encontrado = False
    for fila in proveedores:
        if fila.get("proveedor_id") == proveedor_id:
            for col in COLUMNAS["proveedores"]:
                if col in datos and col != "proveedor_id":
                    fila[col] = datos[col]
            encontrado = True
            break
    if not encontrado:
        return _respuesta(404, {"errores": ["No se encontro un proveedor con ese identificador."]})
    _escribir_csv(RUTAS["proveedores"], COLUMNAS["proveedores"], proveedores)

    # Si se envian listas nuevas de asociaciones, se reemplazan por completo (no se hace
    # diff incremental: es mas simple y suficiente para el alcance de este modulo).
    if any(k in datos for k in ("categorias_proveedor_ids", "categorias_producto_ids", "producto_ids")):
        categorias_proveedor_ids = datos.get("categorias_proveedor_ids") or []
        categorias_producto_ids = datos.get("categorias_producto_ids") or []
        producto_ids = datos.get("producto_ids") or []

        errores = _validar_asociaciones_proveedor(
            categorias_proveedor_ids, categorias_producto_ids, producto_ids
        )
        if errores:
            return _respuesta(400, {"errores": errores})

        _reemplazar_relaciones(
            RUTA_PROVEEDOR_CATEGORIA_PROVEEDOR, COLUMNAS_PROVEEDOR_CATEGORIA_PROVEEDOR,
            proveedor_id, "categoria_proveedor_id", categorias_proveedor_ids,
        )
        _reemplazar_relaciones(
            RUTA_PROVEEDOR_CATEGORIA_PRODUCTO, COLUMNAS_PROVEEDOR_CATEGORIA_PRODUCTO,
            proveedor_id, "categoria_id", categorias_producto_ids,
        )
        _reemplazar_relaciones(
            RUTA_PROVEEDOR_X_PRODUCTO, COLUMNAS_PROVEEDOR_X_PRODUCTO,
            proveedor_id, "producto_id", producto_ids,
        )

    if any(k in datos for k in ("nombre_contacto", "telefonos", "correos")):
        contactos = _leer_csv(RUTA_CONTACTO_PROVEEDOR)
        contactos = [c for c in contactos if c.get("proveedor_id") != proveedor_id]
        if datos.get("nombre_contacto") or datos.get("telefonos") or datos.get("correos"):
            contactos.append({
                "proveedor_id": proveedor_id,
                "nombre_contacto": datos.get("nombre_contacto", ""),
                "telefonos": datos.get("telefonos", ""),
                "correos": datos.get("correos", ""),
            })
        _escribir_csv(RUTA_CONTACTO_PROVEEDOR, COLUMNAS_CONTACTO_PROVEEDOR, contactos)

    return _respuesta(200, {"mensaje": "Proveedor actualizado correctamente."})


def lambda_handler(event, context):
    if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return _respuesta(200, {})

    try:
        cuerpo = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _respuesta(400, {"errores": ["El cuerpo de la solicitud no es un JSON valido."]})

    if cuerpo.get("codigo_acceso") != ACCESS_CODE:
        return _respuesta(403, {"errores": ["Codigo de acceso invalido."]})

    entidad = cuerpo.get("entidad")
    accion = cuerpo.get("accion")
    datos = cuerpo.get("datos", {})

    if entidad not in RUTAS and entidad not in RUTAS_LECTURA:
        return _respuesta(400, {"errores": ["Entidad no reconocida."]})

    if accion == "listar":
        return _manejar_listar(entidad)

    if entidad not in RUTAS:
        return _respuesta(400, {"errores": [f"La entidad '{entidad}' es de solo lectura."]})

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
