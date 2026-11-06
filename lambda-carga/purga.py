"""Purga de runs antiguos: conserva los 14 mas recientes y todo lo que Glue o el estado referencian.

Handler: lambda_handler. Variables: BUCKET_NAME, GLUE_DATABASE, PURGA_MODO (simulacion | borrar).
El evento se ignora. En simulacion se registra purga_plan y no se llama a delete_objects.
"""

import os
import re
from dataclasses import dataclass
from functools import partial
from typing import Any, Callable, Iterator

from catalogo_glue import CatalogoGlue
from errores import CargaError
from estado_s3 import PREFIJO_ETL, EstadoS3, run_ids_en
from observabilidad import registrar
from runner import Config

RUNS_CONSERVADOS = 14
TOPE_OBJETOS = 5000
LOTE_BORRADO = 1000
MODOS = ("simulacion", "borrar")
PREFIJOS_RUNS = ("analytics/runs/", "curated/runs/")
RUN_ID_RE = re.compile(r"[0-9]{14}")
PREVIO_CLAVE_RE = re.compile(re.escape(PREFIJO_ETL) + r"previos_([0-9]{14})\.json")
CLAVE_PERMITIDA_RE = re.compile(r"(analytics|curated)/runs/([0-9]{14})/")


@dataclass(frozen=True)
class DependenciasPurga:
    s3: Any
    glue: Any
    config: Config


def lambda_handler(event: dict, context: Any) -> dict:
    return ejecutar_purga(os.environ.get("PURGA_MODO", ""), crear_dependencias())


def crear_dependencias() -> DependenciasPurga:
    import boto3

    return DependenciasPurga(
        s3=boto3.client("s3"),
        glue=boto3.client("glue"),
        config=Config.desde_entorno(),
    )


def ejecutar_purga(modo: str, deps: DependenciasPurga) -> dict:
    if modo not in MODOS:
        raise CargaError("PURGA_MODO_INVALIDO")
    previos = _ids_previos(deps)
    if len(previos) < RUNS_CONSERVADOS:
        registrar("purga_plan", modo=modo, corte_run_id=None, protegidos=[], a_borrar=[], tope_objetos=TOPE_OBJETOS)
        return {"estado": "sin_corte"}
    corte = previos[RUNS_CONSERVADOS - 1]
    protegidos = _protegidos(deps, previos)
    candidatos = sorted(run for run in _ids_runs(deps) if run < corte and run not in protegidos)
    seleccion = _seleccionar(deps, candidatos)
    registrar(
        "purga_plan",
        modo=modo,
        corte_run_id=corte,
        protegidos=sorted(protegidos),
        a_borrar=_resumen(seleccion),
        tope_objetos=TOPE_OBJETOS,
    )
    if modo == "simulacion":
        return {"estado": "simulacion", "corte_run_id": corte, "objetos": len(seleccion)}
    admitida = partial(_clave_permitida, corte=corte, protegidos=protegidos)
    objetos, bytes_borrados, errores = _borrar(deps, seleccion, admitida)
    registrar("purga_resultado", modo=modo, borrados_objetos=objetos, borrados_bytes=bytes_borrados, errores=errores)
    if errores:
        raise CargaError("BORRADO_PARCIAL")
    return {"estado": "borrado", "corte_run_id": corte, "objetos": objetos, "bytes": bytes_borrados}


def _protegidos(deps: DependenciasPurga, previos: list[str]) -> set[str]:
    estado = EstadoS3(deps.s3, deps.config.bucket)
    ultimo = estado.leer_ultimo_run()
    protegidos = _ids_de_ultimo(ultimo) if ultimo is not None else set()
    for previo in previos[:RUNS_CONSERVADOS]:
        protegidos |= _ids_de_previo(estado, previo)
    referenciados = CatalogoGlue(deps.glue, deps.config.base).run_ids_referenciados()
    if not referenciados and ultimo is None:
        raise CargaError("CONJUNTO_VIVO_VACIO")
    return protegidos | referenciados


def _ids_de_ultimo(ultimo: dict) -> set[str]:
    ids = {ultimo["run_id"]}
    if ultimo.get("previo_run_id"):
        ids.add(ultimo["previo_run_id"])
    for ubicacion in ultimo["tablas"].values():
        ids |= run_ids_en(ubicacion)
    return ids


def _ids_de_previo(estado: EstadoS3, previo: str) -> set[str]:
    try:
        doc = estado.leer_json(f"{PREFIJO_ETL}previos_{previo}.json")
        ids = {previo}
        for datos in doc["tablas"].values():
            ids |= run_ids_en(datos["location_previa"])
    except (AttributeError, KeyError, TypeError, ValueError) as error:
        raise CargaError("PREVIO_ILEGIBLE") from error
    return ids


def _ids_previos(deps: DependenciasPurga) -> list[str]:
    ids = set()
    for pagina in _paginas(deps, Prefix=f"{PREFIJO_ETL}previos_"):
        for objeto in pagina.get("Contents", []):
            coincidencia = PREVIO_CLAVE_RE.fullmatch(objeto["Key"])
            if coincidencia:
                ids.add(coincidencia.group(1))
    return sorted(ids, reverse=True)


def _ids_runs(deps: DependenciasPurga) -> set[str]:
    ids = set()
    for raiz in PREFIJOS_RUNS:
        for pagina in _paginas(deps, Prefix=raiz, Delimiter="/"):
            for comun in pagina.get("CommonPrefixes", []):
                nombre = comun["Prefix"].rstrip("/").rsplit("/", 1)[-1]
                if RUN_ID_RE.fullmatch(nombre):
                    ids.add(nombre)
    return ids


def _seleccionar(deps: DependenciasPurga, candidatos: list[str]) -> list[tuple[str, str, int]]:
    seleccion: list[tuple[str, str, int]] = []
    for run in candidatos:
        for clave, tamano in _objetos_run(deps, run):
            if len(seleccion) >= TOPE_OBJETOS:
                return seleccion
            seleccion.append((run, clave, tamano))
    return seleccion


def _objetos_run(deps: DependenciasPurga, run: str) -> Iterator[tuple[str, int]]:
    for raiz in PREFIJOS_RUNS:
        for pagina in _paginas(deps, Prefix=f"{raiz}{run}/"):
            for objeto in pagina.get("Contents", []):
                yield objeto["Key"], objeto["Size"]


def _resumen(seleccion: list[tuple[str, str, int]]) -> list[dict]:
    acumulado: dict[str, tuple[int, int]] = {}
    for run, _, tamano in seleccion:
        objetos, bytes_ = acumulado.get(run, (0, 0))
        acumulado[run] = (objetos + 1, bytes_ + tamano)
    return [
        {"run_id": run, "objetos": objetos, "bytes": bytes_}
        for run, (objetos, bytes_) in acumulado.items()
    ]


def _borrar(
    deps: DependenciasPurga, seleccion: list[tuple[str, str, int]], admitida: Callable[[str], bool]
) -> tuple[int, int, list[dict]]:
    tamanos = {clave: tamano for _, clave, tamano in seleccion}
    if not all(admitida(clave) for clave in tamanos):
        raise CargaError("CLAVE_NO_PERMITIDA")
    borrados: list[int] = []
    errores: list[dict] = []
    for lote in _lotes(list(tamanos), LOTE_BORRADO):
        respuesta = deps.s3.delete_objects(
            Bucket=deps.config.bucket,
            Delete={"Objects": [{"Key": clave} for clave in lote]},
        )
        borrados += [tamanos[entrada["Key"]] for entrada in respuesta.get("Deleted", [])]
        errores += respuesta.get("Errors", [])
        if errores:
            break
    return len(borrados), sum(borrados), errores


def _clave_permitida(clave: str, corte: str, protegidos: set[str]) -> bool:
    coincidencia = CLAVE_PERMITIDA_RE.match(clave)
    if coincidencia is None:
        return False
    run_id = coincidencia.group(2)
    return run_id < corte and run_id not in protegidos


def _lotes(elementos: list[str], tamano: int) -> Iterator[list[str]]:
    for inicio in range(0, len(elementos), tamano):
        yield elementos[inicio:inicio + tamano]


def _paginas(deps: DependenciasPurga, **filtros: Any) -> Iterator[dict]:
    siguiente = None
    while True:
        extra = {"ContinuationToken": siguiente} if siguiente else {}
        pagina = deps.s3.list_objects_v2(Bucket=deps.config.bucket, **filtros, **extra)
        yield pagina
        siguiente = pagina.get("NextContinuationToken")
        if not siguiente:
            return
