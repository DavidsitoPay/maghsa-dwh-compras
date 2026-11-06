"""Lock de la carga en S3 con escrituras condicionales (If-Match / If-None-Match).

No usa DeleteObject: liberar es escribir el lock como `free`.
"""

import json
from datetime import datetime, timedelta

from errores import CargaError, codigo_error
from estado_s3 import PREFIJO_ETL, leer_objeto
from observabilidad import registrar
from reloj import Reloj, formato_iso

CLAVE_LOCK = f"{PREFIJO_ETL}lock.json"
VIDA_LOCK_S = 900
CODIGOS_CONFLICTO = {"PreconditionFailed", "ConditionalRequestConflict", "NoSuchKey"}


def soporta_if_match(s3) -> bool:
    miembros = s3.meta.service_model.operation_model("PutObject").input_shape.members
    return {"IfMatch", "IfNoneMatch"} <= set(miembros)


class LockS3:
    def __init__(self, s3, bucket: str, reloj: Reloj):
        self._s3 = s3
        self._bucket = bucket
        self._reloj = reloj
        self._etag: str | None = None

    def adquirir(self) -> bool:
        actual = leer_objeto(self._s3, self._bucket, CLAVE_LOCK)
        if actual is None:
            return self._tomar({"IfNoneMatch": "*"})
        cuerpo, etag = actual
        if self._vigente(cuerpo):
            return False
        return self._tomar({"IfMatch": etag})

    def renovar(self, run_id: str) -> None:
        etag = self._escribir("busy", run_id, {"IfMatch": self._etag})
        if etag is None:
            raise CargaError("LOCK_PERDIDO")
        self._etag = etag

    def liberar(self) -> None:
        if self._escribir("free", None, {"IfMatch": self._etag}) is None:
            registrar("lock_liberacion_412")

    def _tomar(self, condicion: dict) -> bool:
        etag = self._escribir("busy", None, condicion)
        if etag is None:
            return False
        self._etag = etag
        return True

    def _vigente(self, cuerpo: bytes) -> bool:
        try:
            doc = json.loads(cuerpo)
            expira = datetime.fromisoformat(doc["expira_utc"])
            if expira.tzinfo is None:
                raise ValueError("expira_utc sin zona horaria")
        except (ValueError, KeyError, TypeError):
            registrar("lock_ilegible")
            return False
        return doc.get("estado") == "busy" and expira > self._reloj.ahora_utc()

    def _escribir(self, estado: str, run_id: str | None, condicion: dict) -> str | None:
        ahora = self._reloj.ahora_utc()
        cuerpo = {
            "estado": estado,
            "run_id": run_id,
            "ts_utc": formato_iso(ahora),
            "expira_utc": formato_iso(ahora + timedelta(seconds=VIDA_LOCK_S)),
        }
        try:
            respuesta = self._s3.put_object(
                Bucket=self._bucket,
                Key=CLAVE_LOCK,
                Body=json.dumps(cuerpo).encode("utf-8"),
                ContentType="application/json",
                **condicion,
            )
        except Exception as error:
            if codigo_error(error) in CODIGOS_CONFLICTO:
                return None
            raise
        return respuesta["ETag"]
