"""Intento de carga: etapas de sentencias, compuertas, publicacion, rollback y limpieza.

Cada intento tiene su run_id; el presupuesto de tiempo (t0) es el de la corrida completa.
"""

from dataclasses import dataclass, field
from datetime import datetime

from athena_ejecutor import EjecutorAthena, Resultado
from catalogo_glue import CatalogoGlue
from compuertas import ResultadoCompuerta, evaluar
from errores import CargaError
from estado_s3 import EstadoS3
from observabilidad import BYTES_POR_GB, registrar
from reloj import Reloj, formato_iso
from sql_etl import MarcaGate, Sentencia, renderizar
from tablas import HECHOS, TABLAS_VIVAS

PRESUPUESTO_S = 840
LIMITE_DURO_S = 880
TOPE_SENTENCIA_S = 240
MIN_PUBLICAR_S = 90
REINTENTABLES = {"G2.fk", "G2.conteo"}
CLAVE_PUBLICAR = "14"
CLAVE_HECHOS_PROYECCION = "14p"
CLAVE_HECHOS_RECREATE = "14r"
CLAVE_LIMPIEZA = "99"


@dataclass
class Corrida:
    bucket: str
    reloj: Reloj
    ejecutor: EjecutorAthena
    estado: EstadoS3
    catalogo: CatalogoGlue
    orden: list[str]
    plantillas: dict[str, list[Sentencia]]
    forzar_g3: bool
    t0: float
    run_id: str = ""
    intento: int = 0
    limite_total_s: float = PRESUPUESTO_S
    contador: int = 0
    escaneo_bytes: int = 0
    filas_hechos: int = 0
    hechos_modo: str = ""
    previas: dict[str, str] = field(default_factory=dict)
    publicadas: list[str] = field(default_factory=list)
    confirmado: bool = False
    rollback_fallido: bool = False

    def reiniciar(self, run_id: str, intento: int) -> None:
        self.run_id = run_id
        self.intento = intento
        self.limite_total_s = PRESUPUESTO_S
        self.contador = 0
        self.filas_hechos = 0
        self.hechos_modo = ""
        self.previas = {}
        self.publicadas = []
        self.confirmado = False

    def restante(self) -> float:
        return self.limite_total_s - (self.reloj.monotonico() - self.t0)


def ejecutar_intento(c: Corrida) -> None:
    inicio = c.reloj.ahora_utc()
    estado_log = "fallo"
    codigo_fallo = None
    try:
        _ejecutar_etapas(c)
        c.confirmado = True
        _confirmar(c, inicio)
        estado_log = "ok"
    except Exception as error:
        codigo_fallo = getattr(error, "codigo", type(error).__name__)
        if c.publicadas and not c.confirmado:
            _revertir_sin_ocultar(c)
            estado_log = "rollback"
        raise
    finally:
        c.limite_total_s = LIMITE_DURO_S
        _limpiar(c)
        _registrar_cierre(c, estado_log, codigo_fallo)


def _ejecutar_etapas(c: Corrida) -> None:
    for clave in c.orden:
        if clave == CLAVE_LIMPIEZA:
            continue
        if clave == CLAVE_PUBLICAR:
            _publicar(c)
        else:
            _ejecutar_clave(c, clave)


def _ejecutar_clave(c: Corrida, clave: str) -> None:
    for sentencia in c.plantillas[clave]:
        resultado = _enviar(c, sentencia, _valores(c))
        if sentencia.marca is not None:
            _verificar_compuerta(c, sentencia.marca, evaluar(c.ejecutor.filas(resultado.query_id)))


def _verificar_compuerta(c: Corrida, marca: MarcaGate, evaluacion: ResultadoCompuerta) -> None:
    _registrar_filas(c, evaluacion.columnas)
    campos = {"run_id": c.run_id, "id": marca.id, "columnas": evaluacion.columnas}
    if evaluacion.ok:
        registrar("compuerta", resultado="ok", **campos)
        return
    if marca.forzable and c.forzar_g3:
        registrar("compuerta", resultado="falla", forzada=True, motivo=evaluacion.motivo, **campos)
        return
    registrar("compuerta", resultado="falla", motivo=evaluacion.motivo, **campos)
    raise CargaError(
        "COMPUERTA_FALLIDA",
        reintentable=marca.id in REINTENTABLES,
        motivo=evaluacion.motivo,
    )


def _registrar_filas(c: Corrida, columnas: dict) -> None:
    if isinstance(columnas.get("info_filas_nuevo"), int):
        c.filas_hechos = columnas["info_filas_nuevo"]
    elif isinstance(columnas.get("info_filas"), int):
        c.filas_hechos = columnas["info_filas"]


def _enviar(c: Corrida, sentencia: Sentencia, valores: dict[str, str]) -> Resultado:
    c.contador += 1
    restante = c.restante()
    if restante <= 0:
        raise CargaError("PRESUPUESTO_AGOTADO")
    sql = renderizar(sentencia, valores)
    token = f"maghsa-carga-{c.run_id}-{c.contador:05d}"  # ClientRequestToken: Athena exige 32-128 caracteres
    campos = {
        "run_id": c.run_id,
        "intento": c.intento,
        "archivo": sentencia.archivo,
        "indice": c.contador,
        "tipo": sentencia.tipo,
        "tabla": sentencia.tabla,
    }
    try:
        resultado = c.ejecutor.ejecutar(sql, token, min(TOPE_SENTENCIA_S, restante))
    except CargaError as error:
        registrar("sentencia", estado="fallo", motivo=error.motivo or error.codigo, **campos)
        raise
    c.escaneo_bytes += resultado.scan_bytes
    registrar(
        "sentencia",
        estado=resultado.estado,
        query_id=resultado.query_id,
        scan_bytes=resultado.scan_bytes,
        ms_motor=resultado.ms_motor,
        ms_total=resultado.ms_total,
        motivo=resultado.motivo,
        **campos,
    )
    return resultado


def _publicar(c: Corrida) -> None:
    if c.restante() < MIN_PUBLICAR_S:
        raise CargaError("PRESUPUESTO_AGOTADO")
    previas = {tabla: c.catalogo.ubicacion(tabla) for tabla in TABLAS_VIVAS}
    if any(not ubicacion.startswith(f"s3://{c.bucket}/") or "'" in ubicacion for ubicacion in previas.values()):
        raise CargaError("UBICACION_PREVIA_INVALIDA")
    hechos_modo = c.catalogo.hechos_modo()
    # Los previos se escriben antes de cualquier ALTER: sin ellos no hay rollback.
    c.estado.escribir_previos(
        c.run_id,
        {
            "schema": 1,
            "run_id": c.run_id,
            "creado_utc": formato_iso(c.reloj.ahora_utc()),
            "hechos_modo": hechos_modo,
            "tablas": {tabla: {"location_previa": ubicacion} for tabla, ubicacion in previas.items()},
        },
    )
    c.previas = previas
    c.hechos_modo = hechos_modo
    for sentencia in c.plantillas[CLAVE_PUBLICAR]:
        c.publicadas.append(sentencia.tabla)
        _enviar(c, sentencia, _valores(c))
    c.publicadas.append(HECHOS)
    clave_hechos = CLAVE_HECHOS_PROYECCION if hechos_modo == "proyeccion" else CLAVE_HECHOS_RECREATE
    for sentencia in c.plantillas[clave_hechos]:
        _enviar(c, sentencia, _valores(c))
    _verificar_publicacion(c)


def _verificar_publicacion(c: Corrida) -> None:
    for tabla in c.publicadas:
        if c.catalogo.ubicacion(tabla).rstrip("/") != _ruta_run(c, tabla):
            raise CargaError("PUBLICACION_FALLIDA")


def _revertir_sin_ocultar(c: Corrida) -> None:
    try:
        _revertir(c)
    except Exception as error:
        c.rollback_fallido = True
        registrar("rollback_error", run_id=c.run_id, tabla=None, motivo=str(error))


def _revertir(c: Corrida) -> None:
    c.limite_total_s = LIMITE_DURO_S
    for tabla in reversed(c.publicadas):
        try:
            _revertir_tabla(c, tabla)
        except Exception as error:
            registrar("rollback_error", run_id=c.run_id, tabla=tabla, motivo=str(error))
    fallidas = [
        tabla
        for tabla in c.publicadas
        if c.catalogo.ubicacion(tabla).rstrip("/") != c.previas[tabla].rstrip("/")
    ]
    if fallidas:
        c.rollback_fallido = True
        registrar("rollback_fallido", run_id=c.run_id, tablas=fallidas)


def _revertir_tabla(c: Corrida, tabla: str) -> None:
    previa = c.previas[tabla]
    valores = _valores(c, location_hechos=previa)
    if tabla == HECHOS and c.hechos_modo == "recreate":
        for sentencia in c.plantillas[CLAVE_HECHOS_RECREATE]:
            _enviar(c, sentencia, valores)
        return
    alter = Sentencia("rollback", f"ALTER TABLE {tabla} SET LOCATION '{previa}'", None, "DDL", tabla)
    _enviar(c, alter, valores)


def _limpiar(c: Corrida) -> None:
    for sentencia in c.plantillas[CLAVE_LIMPIEZA]:
        try:
            _enviar(c, sentencia, _valores(c))
        except Exception as error:
            if isinstance(error, CargaError) and error.codigo == "PRESUPUESTO_AGOTADO":
                return
            registrar("limpieza_fallida", run_id=c.run_id, archivo=sentencia.archivo, motivo=str(error))


def _confirmar(c: Corrida, inicio: datetime) -> None:
    previo = c.estado.leer_ultimo_run()
    c.estado.escribir_ultimo_run(
        {
            "schema": 1,
            "run_id": c.run_id,
            "inicio_utc": formato_iso(inicio),
            "fin_utc": formato_iso(c.reloj.ahora_utc()),
            "estado": "ok",
            "intentos": c.intento,
            "hechos_modo": c.hechos_modo,
            "filas_hechos": c.filas_hechos,
            "previo_run_id": previo["run_id"] if previo else None,
            "tablas": {tabla: f"{_ruta_run(c, tabla)}/" for tabla in TABLAS_VIVAS},
        }
    )


def _registrar_cierre(c: Corrida, estado_log: str, codigo_fallo: str | None) -> None:
    cierre = {
        "run_id": c.run_id,
        "intento": c.intento,
        "estado": estado_log,
        "hechos_modo": c.hechos_modo,
        "duracion_s": c.reloj.monotonico() - c.t0,
        "escaneo_gb": c.escaneo_bytes / BYTES_POR_GB,
        "filas_hechos": c.filas_hechos,
        "error": codigo_fallo,
    }
    registrar("corrida", **cierre)
    try:
        c.estado.escribir_log_corrida(c.run_id, cierre)
    except Exception as error:
        registrar("log_corrida_fallido", run_id=c.run_id, motivo=str(error))


def _valores(c: Corrida, location_hechos: str | None = None) -> dict[str, str]:
    return {
        "bucket": c.bucket,
        "run_id": c.run_id,
        "location_hechos": location_hechos or f"{_ruta_run(c, HECHOS)}/",
    }


def _ruta_run(c: Corrida, tabla: str) -> str:
    return f"s3://{c.bucket}/analytics/runs/{c.run_id}/{tabla}"
