"""Reloj inyectable: las pruebas avanzan el tiempo sin esperar de verdad."""

import time
from datetime import datetime, timezone


class Reloj:
    def ahora_utc(self) -> datetime:
        return datetime.now(timezone.utc)

    def monotonico(self) -> float:
        return time.monotonic()

    def dormir(self, segundos: float) -> None:
        time.sleep(segundos)


def formato_iso(instante: datetime) -> str:
    return instante.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
