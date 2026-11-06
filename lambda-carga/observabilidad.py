"""Logs JSON de una linea y metricas EMF (CloudWatch) del namespace MAGHSA/CargaDWH.

La linea EMF se imprime como JSON puro: no pasa por `logging`.
"""

import json
from dataclasses import dataclass
from datetime import datetime

NAMESPACE = "MAGHSA/CargaDWH"
BYTES_POR_GB = 10**9
UNIDADES = {
    "RunOK": "Count",
    "Duracion_s": "Seconds",
    "Escaneo_GB": "Gigabytes",
    "Filas_hechos": "Count",
    "RollbackFallido": "Count",
}


@dataclass(frozen=True)
class MetricasCorrida:
    run_ok: bool
    duracion_s: float
    escaneo_gb: float
    filas_hechos: int
    rollback_fallido: bool


def registrar(evento: str, **campos) -> None:
    print(json.dumps({"evento": evento, **campos}, default=str, ensure_ascii=False))


def emitir_metricas(metricas: MetricasCorrida, ahora: datetime) -> None:
    valores = {
        "RunOK": int(metricas.run_ok),
        "Duracion_s": metricas.duracion_s,
        "Escaneo_GB": metricas.escaneo_gb,
        "Filas_hechos": metricas.filas_hechos,
        "RollbackFallido": int(metricas.rollback_fallido),
    }
    definicion = {
        "_aws": {
            "Timestamp": int(ahora.timestamp() * 1000),
            "CloudWatchMetrics": [
                {
                    "Namespace": NAMESPACE,
                    "Dimensions": [[]],
                    "Metrics": [{"Name": nombre, "Unit": unidad} for nombre, unidad in UNIDADES.items()],
                }
            ],
        },
        **valores,
    }
    print(json.dumps(definicion))
