"""Estado de la carga en athena-results/etl/: ultimo_run, previos, lock y log de cada corrida."""

import json
import re

from errores import codigo_error

PREFIJO_ETL = "athena-results/etl/"
CLAVE_ULTIMO_RUN = f"{PREFIJO_ETL}ultimo_run.json"
RUN_EN_RUTA = re.compile(r"/runs/([0-9]{14})(?=/|$)")


def run_ids_en(texto: str) -> set[str]:
    return set(RUN_EN_RUTA.findall(texto))


def leer_objeto(s3, bucket: str, clave: str) -> tuple[bytes, str] | None:
    # Sin ListBucket una clave ausente da AccessDenied: la existencia se decide con el listado.
    listado = s3.list_objects_v2(Bucket=bucket, Prefix=clave, MaxKeys=1)
    if not any(objeto["Key"] == clave for objeto in listado.get("Contents", [])):
        return None
    try:
        objeto = s3.get_object(Bucket=bucket, Key=clave)
    except Exception as error:
        if codigo_error(error) == "NoSuchKey":
            return None
        raise
    return objeto["Body"].read(), objeto["ETag"]


class EstadoS3:
    def __init__(self, s3, bucket: str):
        self._s3 = s3
        self._bucket = bucket

    def leer_json(self, clave: str) -> dict | None:
        objeto = leer_objeto(self._s3, self._bucket, clave)
        return None if objeto is None else json.loads(objeto[0])

    def leer_ultimo_run(self) -> dict | None:
        return self.leer_json(CLAVE_ULTIMO_RUN)

    def escribir_previos(self, run_id: str, doc: dict) -> None:
        self._escribir(f"{PREFIJO_ETL}previos_{run_id}.json", doc)

    def escribir_ultimo_run(self, doc: dict) -> None:
        self._escribir(CLAVE_ULTIMO_RUN, doc)

    def escribir_log_corrida(self, run_id: str, doc: dict) -> None:
        self._escribir(f"{PREFIJO_ETL}runs/{run_id}.json", doc)

    def _escribir(self, clave: str, doc: dict) -> None:
        self._s3.put_object(
            Bucket=self._bucket,
            Key=clave,
            Body=json.dumps(doc).encode("utf-8"),
            ContentType="application/json",
        )
