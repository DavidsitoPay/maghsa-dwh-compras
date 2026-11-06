"""Ejecucion de sentencias en Athena: token idempotente, reintento por throttling y sondeo."""

from dataclasses import dataclass

from errores import CATEGORIA_ERROR_SISTEMA, CargaError, codigo_error
from reloj import Reloj

CODIGO_THROTTLING = "TooManyRequestsException"
BACKOFF_S = (1, 2, 4, 8, 16)
SONDEO_INICIAL_S = 1
SONDEO_FACTOR = 1.5
SONDEO_TOPE_S = 5
ESTADOS_FALLO = ("FAILED", "CANCELLED")


@dataclass(frozen=True)
class ConfigAthena:
    workgroup: str
    base: str
    salida: str


@dataclass(frozen=True)
class Resultado:
    query_id: str
    estado: str
    scan_bytes: int
    ms_motor: int
    ms_total: int
    motivo: str | None
    categoria_error: int | None


class EjecutorAthena:
    def __init__(self, athena, reloj: Reloj, config: ConfigAthena):
        self._athena = athena
        self._reloj = reloj
        self._config = config

    def ejecutar(self, sql: str, token: str, tope_s: float) -> Resultado:
        inicio = self._reloj.monotonico()
        query_id = self._con_backoff(lambda: self._iniciar(sql, token))["QueryExecutionId"]
        espera = SONDEO_INICIAL_S
        while True:
            ejecucion = self._con_backoff(
                lambda: self._athena.get_query_execution(QueryExecutionId=query_id)
            )["QueryExecution"]
            estado = ejecucion["Status"]["State"]
            if estado == "SUCCEEDED":
                return _resultado(query_id, ejecucion)
            if estado in ESTADOS_FALLO:
                raise _error_fallo(ejecucion)
            if self._reloj.monotonico() - inicio > tope_s:
                self.detener(query_id)
                raise CargaError("SENTENCIA_TIMEOUT")
            self._reloj.dormir(espera)
            espera = min(espera * SONDEO_FACTOR, SONDEO_TOPE_S)

    def filas(self, query_id: str) -> list[list[str | None]]:
        resultado: list[list[str | None]] = []
        siguiente = None
        while True:
            pagina = self._con_backoff(lambda: self._pagina(query_id, siguiente))
            for fila in pagina["ResultSet"]["Rows"]:
                resultado.append([dato.get("VarCharValue") for dato in fila["Data"]])
            siguiente = pagina.get("NextToken")
            if not siguiente:
                return resultado

    def detener(self, query_id: str) -> None:
        self._athena.stop_query_execution(QueryExecutionId=query_id)

    def _iniciar(self, sql: str, token: str):
        return self._athena.start_query_execution(
            QueryString=sql,
            ClientRequestToken=token,  # Athena exige 32-128 caracteres
            WorkGroup=self._config.workgroup,
            QueryExecutionContext={"Database": self._config.base},
            ResultConfiguration={"OutputLocation": self._config.salida},
        )

    def _pagina(self, query_id: str, siguiente: str | None):
        argumentos = {"QueryExecutionId": query_id}
        if siguiente:
            argumentos["NextToken"] = siguiente
        return self._athena.get_query_results(**argumentos)

    def _con_backoff(self, operacion):
        for espera in BACKOFF_S:
            try:
                return operacion()
            except Exception as error:
                if codigo_error(error) != CODIGO_THROTTLING:
                    raise
                self._reloj.dormir(espera)
        try:
            return operacion()
        except Exception as error:
            if codigo_error(error) == CODIGO_THROTTLING:
                raise CargaError("THROTTLING_AGOTADO") from error
            raise


def _resultado(query_id: str, ejecucion: dict) -> Resultado:
    estadisticas = ejecucion.get("Statistics", {})
    return Resultado(
        query_id=query_id,
        estado=ejecucion["Status"]["State"],
        scan_bytes=estadisticas.get("DataScannedInBytes", 0),
        ms_motor=estadisticas.get("EngineExecutionTimeInMillis", 0),
        ms_total=estadisticas.get("TotalExecutionTimeInMillis", 0),
        motivo=ejecucion["Status"].get("StateChangeReason"),
        categoria_error=None,
    )


def _error_fallo(ejecucion: dict) -> CargaError:
    estado = ejecucion["Status"]
    categoria = estado.get("AthenaError", {}).get("ErrorCategory")
    return CargaError(
        "SENTENCIA_FALLIDA",
        reintentable=categoria == CATEGORIA_ERROR_SISTEMA,
        motivo=estado.get("StateChangeReason"),
    )
