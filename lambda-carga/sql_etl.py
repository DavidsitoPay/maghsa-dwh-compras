"""Lectura de athena/etl/: orden de ejecucion, sentencias, marcas de compuerta y placeholders.

Marca de compuerta: lineas `-- GATE: <id> <ZERO|ZERO_FORZABLE>` contiguas encima de un SELECT.
"""

import re
from dataclasses import dataclass
from pathlib import Path

from errores import CargaError
from tablas import HECHOS, TABLAS_VIVAS

ARCHIVO_ORDEN = "orden.txt"
VALORES_PRUEBA = {
    "bucket": "bucket-de-prueba",
    "run_id": "20000101000000",
    "location_hechos": "s3://bucket-de-prueba/analytics/runs/20000101000000/hechos_compras/",
}
MARCADORES = {
    "<bucket-maghsa-dwh>": "bucket",
    "<run_id>": "run_id",
    "<location_hechos>": "location_hechos",
}
PALABRAS_LECTURA = {"SELECT", "WITH", "SHOW", "DESCRIBE", "EXPLAIN"}
PALABRAS_GATE = {"SELECT", "WITH"}
GATE_PREFIJO = re.compile(r"--\s*GATE:")
GATE_RE = re.compile(r"--\s*GATE:\s*(\S+)\s+(ZERO|ZERO_FORZABLE)\s*$")
PLACEHOLDER_RE = re.compile(r"<[a-z][a-z0-9_-]*>")
CTAS_RE = re.compile(r"CREATE\s+TABLE\b", re.IGNORECASE)
INSERT_RE = re.compile(r"INSERT\b", re.IGNORECASE)
TABLA_RE = re.compile(
    r"(?:CREATE(?:\s+OR\s+REPLACE)?(?:\s+EXTERNAL)?\s+(?:TABLE|VIEW)|INSERT\s+INTO|ALTER\s+TABLE"
    r"|DROP\s+(?:TABLE|VIEW)|MSCK\s+REPAIR\s+TABLE)\s+(?:IF\s+(?:NOT\s+)?EXISTS\s+)?(\w+)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class MarcaGate:
    id: str
    forzable: bool


@dataclass(frozen=True)
class Sentencia:
    archivo: str
    texto: str
    marca: MarcaGate | None
    tipo: str
    tabla: str | None


def clave_archivo(nombre: str) -> str:
    return nombre.removesuffix(".sql").split("_", 1)[0]


def leer_orden(directorio: Path) -> list[str]:
    try:
        lineas = (directorio / ARCHIVO_ORDEN).read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise CargaError("ORDEN_INVALIDO") from error
    limpias = (linea.strip() for linea in lineas)
    return [clave_archivo(linea) for linea in limpias if linea and not linea.startswith("#")]


def dividir_sentencias(archivo: str, texto: str) -> list[Sentencia]:
    sentencias: list[Sentencia] = []
    buffer = ""
    marca_vigente: MarcaGate | None = None
    marca_sentencia: MarcaGate | None = None
    en_comilla = False
    for linea in texto.splitlines():
        inicio = linea.strip()
        if not en_comilla:
            if inicio.startswith("--"):
                if GATE_PREFIJO.match(inicio):
                    marca_vigente = _leer_marca(inicio)
                continue
            if not inicio and not buffer.strip():
                marca_vigente = None
                continue
        fragmentos, en_comilla = _partir_linea(linea, en_comilla)
        for fragmento, cerrado in fragmentos:
            if not buffer.strip() and fragmento.strip():
                marca_sentencia, marca_vigente = marca_vigente, None
            buffer = f"{buffer}\n{fragmento}"
            if cerrado:
                if buffer.strip():
                    sentencias.append(_construir(archivo, buffer.strip(), marca_sentencia))
                buffer = ""
                marca_sentencia = None
    if buffer.strip():
        sentencias.append(_construir(archivo, buffer.strip(), marca_sentencia))
    return sentencias


def cargar_plantillas(directorio: Path) -> tuple[list[str], dict[str, list[Sentencia]]]:
    orden = leer_orden(directorio)
    plantillas = _leer_plantillas(directorio)
    _validar(orden, plantillas)
    return orden, plantillas


def renderizar(sentencia: Sentencia, valores: dict[str, str]) -> str:
    texto = sentencia.texto
    for marcador, clave in MARCADORES.items():
        texto = texto.replace(marcador, valores[clave])
    if PLACEHOLDER_RE.search(texto):
        raise CargaError("PLACEHOLDER_SIN_RESOLVER")
    return texto


def _partir_linea(linea: str, en_comilla: bool) -> tuple[list[tuple[str, bool]], bool]:
    fragmentos: list[tuple[str, bool]] = []
    actual: list[str] = []
    for caracter in linea:
        if caracter == ";" and not en_comilla:
            fragmentos.append(("".join(actual), True))
            actual = []
            continue
        if caracter == "'":
            en_comilla = not en_comilla
        actual.append(caracter)
    fragmentos.append(("".join(actual), False))
    return fragmentos, en_comilla


def _leer_marca(linea: str) -> MarcaGate:
    coincidencia = GATE_RE.match(linea)
    if coincidencia is None:
        raise CargaError("GATE_INVALIDA")
    return MarcaGate(id=coincidencia.group(1), forzable=coincidencia.group(2) == "ZERO_FORZABLE")


def _construir(archivo: str, texto: str, marca: MarcaGate | None) -> Sentencia:
    primera = texto.split(None, 1)[0].upper()
    if marca is not None:
        if primera not in PALABRAS_GATE:
            raise CargaError("GATE_INVALIDA")
        return Sentencia(archivo, texto, marca, "GATE", None)
    if primera in PALABRAS_LECTURA:
        raise CargaError("SELECT_SIN_MARCA")
    if CTAS_RE.match(texto):
        tipo = "CTAS"
    elif INSERT_RE.match(texto):
        tipo = "INSERT"
    else:
        tipo = "DDL"
    coincidencia = TABLA_RE.match(texto)
    tabla = coincidencia.group(1) if coincidencia else None
    return Sentencia(archivo, texto, None, tipo, tabla)


def _leer_plantillas(directorio: Path) -> dict[str, list[Sentencia]]:
    plantillas: dict[str, list[Sentencia]] = {}
    for ruta in sorted(directorio.glob("*.sql")):
        clave = clave_archivo(ruta.name)
        if clave in plantillas:
            raise CargaError("ORDEN_INVALIDO")
        plantillas[clave] = dividir_sentencias(ruta.name, ruta.read_text(encoding="utf-8"))
    return plantillas


def _validar(orden: list[str], plantillas: dict[str, list[Sentencia]]) -> None:
    if "14" not in orden or orden[-2:] != ["15", "99"] or orden.index("14") > orden.index("15"):
        raise CargaError("ORDEN_INVALIDO")
    if "14p" in orden or "14r" in orden or not {"14p", "14r"} <= plantillas.keys():
        raise CargaError("ORDEN_INVALIDO")
    if any(clave not in plantillas for clave in orden):
        raise CargaError("ORDEN_INVALIDO")
    _validar_etapa_14(plantillas["14"])
    for sentencias in plantillas.values():
        for sentencia in sentencias:
            renderizar(sentencia, VALORES_PRUEBA)


def _validar_etapa_14(sentencias: list[Sentencia]) -> None:
    tablas = [sentencia.tabla for sentencia in sentencias]
    esperadas = set(TABLAS_VIVAS) - {HECHOS}
    if (
        len(tablas) != len(esperadas)
        or set(tablas) != esperadas
        or any("SET LOCATION" not in sentencia.texto.upper() for sentencia in sentencias)
    ):
        raise CargaError("ORDEN_INVALIDO")
