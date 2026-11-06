"""Runner de la carga diaria: ejecuta athena/etl/ por orden.txt sobre runs nuevos y publica las 12 tablas.

Variables de entorno:
    BUCKET_NAME       -> bucket del DWH (obligatoria)
    GLUE_DATABASE     -> base de Glue (por defecto compras_dwh)
    ATHENA_WORKGROUP  -> workgroup de Athena (por defecto primary)
    SQL_DIR           -> carpeta de sentencias (por defecto sql/ junto a este modulo)

Evento: {} o {"forzar_g3": bool}. Respuesta: {"estado": "ok" | "omitida", ...}; un fallo lanza CargaError.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from athena_ejecutor import ConfigAthena, EjecutorAthena
from catalogo_glue import CatalogoGlue
from errores import CargaError
from estado_s3 import PREFIJO_ETL, EstadoS3
from intento import PRESUPUESTO_S, Corrida, ejecutar_intento
from lock_s3 import LockS3, soporta_if_match
from observabilidad import BYTES_POR_GB, MetricasCorrida, emitir_metricas, registrar
from reloj import Reloj
from sql_etl import cargar_plantillas

MIN_REINTENTO_S = 420


@dataclass(frozen=True)
class Config:
    bucket: str
    base: str
    workgroup: str
    sql_dir: Path

    @classmethod
    def desde_entorno(cls) -> "Config":
        return cls(
            bucket=os.environ["BUCKET_NAME"],
            base=os.environ.get("GLUE_DATABASE", "compras_dwh"),
            workgroup=os.environ.get("ATHENA_WORKGROUP", "primary"),
            sql_dir=Path(os.environ.get("SQL_DIR", Path(__file__).parent / "sql")),
        )


@dataclass(frozen=True)
class Dependencias:
    athena: Any
    s3: Any
    glue: Any
    reloj: Reloj
    config: Config


def lambda_handler(event: dict, context: Any) -> dict:
    return ejecutar_corrida(event, crear_dependencias())


def crear_dependencias() -> Dependencias:
    import boto3

    return Dependencias(
        athena=boto3.client("athena"),
        s3=boto3.client("s3"),
        glue=boto3.client("glue"),
        reloj=Reloj(),
        config=Config.desde_entorno(),
    )


def ejecutar_corrida(evento: dict, deps: Dependencias) -> dict:
    t0 = deps.reloj.monotonico()
    forzar_g3 = validar_evento(evento)
    if not soporta_if_match(deps.s3):
        raise CargaError("LOCK_NO_SOPORTADO")
    orden, plantillas = cargar_plantillas(deps.config.sql_dir)
    bucket = deps.config.bucket
    lock = LockS3(deps.s3, bucket, deps.reloj)
    if not lock.adquirir():
        registrar("lock_ocupado")
        return {"estado": "omitida", "run_id": None, "intentos": 0, "duracion_s": deps.reloj.monotonico() - t0}
    corrida = Corrida(
        bucket=bucket,
        reloj=deps.reloj,
        ejecutor=EjecutorAthena(
            deps.athena,
            deps.reloj,
            ConfigAthena(
                workgroup=deps.config.workgroup,
                base=deps.config.base,
                salida=f"s3://{bucket}/{PREFIJO_ETL}",
            ),
        ),
        estado=EstadoS3(deps.s3, bucket),
        catalogo=CatalogoGlue(deps.glue, deps.config.base),
        orden=orden,
        plantillas=plantillas,
        forzar_g3=forzar_g3,
        t0=t0,
    )
    ok = False
    try:
        _comprobar_workgroup(deps)
        _ejecutar_con_reintento(corrida, lock)
        ok = True
    finally:
        _cerrar(corrida, lock, ok)
    return {
        "estado": "ok",
        "run_id": corrida.run_id,
        "intentos": corrida.intento,
        "duracion_s": deps.reloj.monotonico() - t0,
    }


def validar_evento(evento: Any) -> bool:
    if not isinstance(evento, dict):
        raise CargaError("EVENTO_INVALIDO")
    if not evento:
        return False
    if set(evento) == {"forzar_g3"} and isinstance(evento["forzar_g3"], bool):
        return evento["forzar_g3"]
    raise CargaError("EVENTO_INVALIDO")


def generar_run_id(reloj: Reloj, anterior: str | None) -> str:
    while True:
        run_id = reloj.ahora_utc().strftime("%Y%m%d%H%M%S")
        if run_id != anterior:
            return run_id
        reloj.dormir(1)


def _comprobar_workgroup(deps: Dependencias) -> None:
    grupo = deps.athena.get_work_group(WorkGroup=deps.config.workgroup)["WorkGroup"]
    if grupo.get("Configuration", {}).get("EnforceWorkGroupConfiguration"):
        raise CargaError("WORKGROUP_ENFORCE")


def _ejecutar_con_reintento(corrida: Corrida, lock: LockS3) -> None:
    anterior = None
    for numero in (1, 2):
        run_id = generar_run_id(corrida.reloj, anterior)
        anterior = run_id
        lock.renovar(run_id)
        corrida.reiniciar(run_id, numero)
        try:
            ejecutar_intento(corrida)
            return
        except CargaError as error:
            if numero == 1 and _puede_reintentar(corrida, error):
                continue
            raise


def _puede_reintentar(corrida: Corrida, error: CargaError) -> bool:
    restante_presupuesto = PRESUPUESTO_S - (corrida.reloj.monotonico() - corrida.t0)
    return error.reintentable and restante_presupuesto >= MIN_REINTENTO_S and not corrida.rollback_fallido


def _cerrar(corrida: Corrida, lock: LockS3, ok: bool) -> None:
    metricas = MetricasCorrida(
        run_ok=ok,
        duracion_s=corrida.reloj.monotonico() - corrida.t0,
        escaneo_gb=corrida.escaneo_bytes / BYTES_POR_GB,
        filas_hechos=corrida.filas_hechos,
        rollback_fallido=corrida.rollback_fallido,
    )
    emitir_metricas(metricas, corrida.reloj.ahora_utc())
    try:
        lock.liberar()
    except Exception as error:
        registrar("lock_liberacion_error", motivo=str(error))
