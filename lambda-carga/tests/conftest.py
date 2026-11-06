"""Fakes locales de S3, Glue, Athena y reloj. Se inyectan por constructor; sin red ni boto3."""

import io
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reloj import formato_iso  # noqa: E402
from runner import Config, Dependencias  # noqa: E402
from tablas import HECHOS, TABLAS_VIVAS  # noqa: E402

BUCKET = "bucket-prueba"
BASE_GLUE = "compras_dwh"
INSTANTE_BASE = datetime(2026, 11, 4, 12, 0, 0, tzinfo=timezone.utc)
RUN_BASE = "20261104120000"
CLAVE_LOCK = "athena-results/etl/lock.json"
CLAVE_ULTIMO = "athena-results/etl/ultimo_run.json"
PREFIJO_PREVIOS = "athena-results/etl/previos_"
GATES_CONTROL = {"ctrl": "0", "info_filas": "99", "info_filas_nuevo": "99"}
BYTES_POR_CONSULTA = 1000
ORDEN_SINTETICO = [
    "01", "02", "03", "04", "05", "06", "09", "10", "11", "12",
    "07a", "07b", "07c", "07d", "08", "13", "14", "15", "99",
]
ARCHIVOS_SINTETICOS = {
    "01": "01_dim_proveedor.sql",
    "02": "02_dim_producto.sql",
    "03": "03_dim_contacto_proveedor.sql",
    "04": "04_puente_proveedor_categoria_proveedor.sql",
    "05": "05_puente_proveedor_categoria_producto.sql",
    "06": "06_puente_proveedor_producto.sql",
    "07a": "07a_hechos_origen.sql",
    "07b": "07b_hechos_validacion.sql",
    "07c": "07c_hechos_carga.sql",
    "07d": "07d_hechos_carga_bloque2.sql",
    "08": "08_dim_tiempo.sql",
    "09": "09_dim_categoria.sql",
    "10": "10_dim_categoria_proveedor.sql",
    "11": "11_dim_unidad_organizacional.sql",
    "12": "12_categoria_proveedor_x_categoria_producto.sql",
    "13": "13_compuertas_publicacion.sql",
    "14": "14_publicar.sql",
    "14p": "14p_publicar_hechos_P.sql",
    "14r": "14r_publicar_hechos_R.sql",
    "15": "15_verificar_publicacion.sql",
    "99": "99_limpieza.sql",
}


class ErrorCliente(Exception):
    def __init__(self, codigo: str):
        super().__init__(codigo)
        self.response = {"Error": {"Code": codigo}}


class FakeReloj:
    def __init__(self):
        self.offset = 0.0
        self.dormidos: list[float] = []

    def ahora_utc(self) -> datetime:
        return INSTANTE_BASE + timedelta(seconds=self.offset)

    def monotonico(self) -> float:
        return self.offset

    def dormir(self, segundos: float) -> None:
        self.dormidos.append(segundos)
        self.offset += segundos

    def avanzar(self, segundos: float) -> None:
        self.offset += segundos


class _Forma:
    def __init__(self, miembros):
        self.members = dict.fromkeys(miembros)


class _ModeloServicio:
    def __init__(self, s3):
        self._s3 = s3

    def operation_model(self, _nombre):
        miembros = {"Bucket", "Key", "Body", "ContentType"}
        if self._s3.soporta_condicionales:
            miembros |= {"IfMatch", "IfNoneMatch"}
        return SimpleNamespace(input_shape=_Forma(miembros))


class FakeS3:
    def __init__(self, eventos, soporta_condicionales=True, ausente_da_403=False, tam_pagina=3):
        self.eventos = eventos
        self.soporta_condicionales = soporta_condicionales
        self.ausente_da_403 = ausente_da_403
        self.tam_pagina = tam_pagina
        self.objetos: dict[str, tuple[bytes, str]] = {}
        self.puts: list[dict] = []
        self.llamadas_delete: list[list[str]] = []
        self.errores_delete: list[dict] | None = None
        self.antes_de_put = None
        self.meta = SimpleNamespace(service_model=_ModeloServicio(self))
        self._contador = 0

    def escribir_directo(self, clave: str, cuerpo: bytes) -> None:
        self._contador += 1
        self.objetos[clave] = (cuerpo, f'"e{self._contador}"')

    def claves(self, prefijo: str = "") -> set[str]:
        return {clave for clave in self.objetos if clave.startswith(prefijo)}

    def leer(self, clave: str) -> dict:
        return json.loads(self.objetos[clave][0])

    def get_object(self, Bucket, Key):
        if Key not in self.objetos:
            raise ErrorCliente("AccessDenied" if self.ausente_da_403 else "NoSuchKey")
        cuerpo, etag = self.objetos[Key]
        return {"Body": io.BytesIO(cuerpo), "ETag": etag}

    def put_object(self, Bucket, Key, Body, ContentType=None, IfMatch=None, IfNoneMatch=None):
        if self.antes_de_put is not None:
            hook, self.antes_de_put = self.antes_de_put, None
            hook(self)
        self.puts.append({"Key": Key, "IfMatch": IfMatch, "IfNoneMatch": IfNoneMatch})
        existe = Key in self.objetos
        if IfNoneMatch == "*" and existe:
            raise ErrorCliente("PreconditionFailed")
        if IfMatch is not None:
            if not existe:
                raise ErrorCliente("NoSuchKey")
            if self.objetos[Key][1] != IfMatch:
                raise ErrorCliente("PreconditionFailed")
        self.escribir_directo(Key, Body)
        self.eventos.append(("put", Key))
        return {"ETag": self.objetos[Key][1]}

    def list_objects_v2(self, Bucket, Prefix="", Delimiter=None, MaxKeys=None, ContinuationToken=None):
        entradas = self._entradas(Prefix, Delimiter)
        tam = MaxKeys or self.tam_pagina
        inicio = int(ContinuationToken or 0)
        respuesta = {"Contents": [], "CommonPrefixes": []}
        for tipo, valor in entradas[inicio:inicio + tam]:
            if tipo == "clave":
                respuesta["Contents"].append({"Key": valor, "Size": len(self.objetos[valor][0])})
            else:
                respuesta["CommonPrefixes"].append({"Prefix": valor})
        if inicio + tam < len(entradas):
            respuesta["IsTruncated"] = True
            respuesta["NextContinuationToken"] = str(inicio + tam)
        return respuesta

    def delete_objects(self, Bucket, Delete):
        claves = [entrada["Key"] for entrada in Delete["Objects"]]
        self.llamadas_delete.append(claves)
        if self.errores_delete is not None:
            errores, self.errores_delete = self.errores_delete, None
            return {"Errors": [errores]}
        for clave in claves:
            self.objetos.pop(clave, None)
        self.eventos.append(("delete", len(claves)))
        return {"Deleted": [{"Key": clave} for clave in claves]}

    def _entradas(self, prefijo: str, delimitador):
        entradas, vistos = [], set()
        for clave in sorted(self.objetos):
            if not clave.startswith(prefijo):
                continue
            resto = clave[len(prefijo):]
            if delimitador and delimitador in resto:
                comun = prefijo + resto.split(delimitador, 1)[0] + delimitador
                if comun not in vistos:
                    vistos.add(comun)
                    entradas.append(("prefijo", comun))
            else:
                entradas.append(("clave", clave))
        return entradas


class FakeGlue:
    def __init__(self):
        self.tablas: dict[str, dict] = {}
        self.particiones: dict[str, list[str]] = {}
        self.llamadas: list[str] = []
        self.fallar: dict[str, Exception] = {}

    def sembrar_legado(self) -> None:
        for tabla in TABLAS_VIVAS:
            self.tablas[tabla] = {"Location": f"s3://{BUCKET}/analytics/{tabla}/", "Parameters": {}}
        self.tablas[HECHOS]["Parameters"] = {"projection.enabled": "true"}

    def ubicacion(self, tabla: str) -> str:
        return self.tablas[tabla]["Location"]

    def aplicar(self, sql: str) -> None:
        alter = re.search(r"ALTER TABLE (\w+) SET LOCATION '([^']+)'", sql)
        if alter and alter.group(1) in self.tablas:
            self.tablas[alter.group(1)]["Location"] = alter.group(2)
            return
        drop = re.search(r"DROP TABLE IF EXISTS (\w+)", sql)
        if drop:
            self.tablas.pop(drop.group(1), None)
            return
        creacion = re.search(r"CREATE EXTERNAL TABLE (\w+) .*LOCATION '([^']+)'", sql, re.S)
        if creacion:
            self.tablas[creacion.group(1)] = {"Location": creacion.group(2), "Parameters": {}}

    def get_table(self, DatabaseName, Name):
        self._llamar("get_table")
        if Name not in self.tablas:
            raise ErrorCliente("EntityNotFoundException")
        return {"Table": self._vista(Name)}

    def get_tables(self, DatabaseName, NextToken=None):
        self._llamar("get_tables")
        nombres = sorted(self.tablas)
        inicio = int(NextToken or 0)
        respuesta = {"TableList": [self._vista(n) for n in nombres[inicio:inicio + 2]]}
        if inicio + 2 < len(nombres):
            respuesta["NextToken"] = str(inicio + 2)
        return respuesta

    def get_partitions(self, DatabaseName, TableName, NextToken=None):
        self._llamar("get_partitions")
        ubicaciones = self.particiones.get(TableName, [])
        inicio = int(NextToken or 0)
        respuesta = {
            "Partitions": [{"StorageDescriptor": {"Location": u}} for u in ubicaciones[inicio:inicio + 1]]
        }
        if inicio + 1 < len(ubicaciones):
            respuesta["NextToken"] = str(inicio + 1)
        return respuesta

    def _vista(self, nombre: str) -> dict:
        datos = self.tablas[nombre]
        return {
            "Name": nombre,
            "StorageDescriptor": {"Location": datos["Location"]},
            "Parameters": dict(datos["Parameters"]),
        }

    def _llamar(self, metodo: str) -> None:
        self.llamadas.append(metodo)
        if metodo in self.fallar:
            raise self.fallar[metodo]


class FakeAthena:
    def __init__(self, glue, reloj, eventos):
        self.glue = glue
        self.reloj = reloj
        self.eventos = eventos
        self.inicios: list[dict] = []
        self.intentos_inicio: list[str] = []
        self.detenidas: list[str] = []
        self.enforce = False
        self.polls_hasta_final = 0
        self._fallas: list[dict] = []
        self._compuertas: list[dict] = []
        self._costos: list[dict] = []
        self._errores: dict[str, list[str]] = {}
        self._colgadas: list[str] = []
        self._ignorar: list[str] = []
        self._por_token: dict[str, str] = {}
        self._estado: dict[str, dict] = {}
        self._filas: dict[str, list[list]] = {}
        self._contador = 0

    def programar_falla(self, patron: str, categoria: int, veces: int = 1) -> None:
        self._fallas.append({"patron": patron, "categoria": categoria, "veces": veces})

    def programar_compuerta(self, patron: str, columnas: dict, veces: int | None = None) -> None:
        self._compuertas.append({"patron": patron, "columnas": columnas, "veces": veces})

    def programar_costo(self, patron: str, segundos: float, veces: int | None = None) -> None:
        self._costos.append({"patron": patron, "segundos": segundos, "veces": veces})

    def programar_error(self, operacion: str, codigo: str, veces: int = 1) -> None:
        self._errores.setdefault(operacion, []).extend([codigo] * veces)

    def colgar(self, patron: str) -> None:
        self._colgadas.append(patron)

    def ignorar_efecto(self, patron: str) -> None:
        self._ignorar.append(patron)

    def start_query_execution(self, QueryString, ClientRequestToken, WorkGroup, QueryExecutionContext, ResultConfiguration):
        self.intentos_inicio.append(ClientRequestToken)
        self._lanzar_error("start")
        if not 32 <= len(ClientRequestToken) <= 128:
            raise ErrorCliente("InvalidRequestException")
        if ClientRequestToken in self._por_token:
            return {"QueryExecutionId": self._por_token[ClientRequestToken]}
        self._contador += 1
        qid = f"q{self._contador}"
        self._por_token[ClientRequestToken] = qid
        self.inicios.append({
            "sql": QueryString,
            "token": ClientRequestToken,
            "workgroup": WorkGroup,
            "base": QueryExecutionContext["Database"],
            "salida": ResultConfiguration["OutputLocation"],
            "query_id": qid,
        })
        self.eventos.append(("athena", QueryString))
        self.reloj.avanzar(self._consumir_costo(QueryString))
        falla = self._buscar(self._fallas, QueryString)
        colgada = any(p in QueryString for p in self._colgadas)
        if falla is None and not any(p in QueryString for p in self._ignorar):
            self.glue.aplicar(QueryString)
        compuerta = self._buscar(self._compuertas, QueryString)
        columnas = compuerta["columnas"] if compuerta else GATES_CONTROL
        self._filas[qid] = [list(columnas), [columnas[c] for c in columnas]]
        self._estado[qid] = {"polls": self.polls_hasta_final, "visto": False, "colgada": colgada, "falla": falla}
        return {"QueryExecutionId": qid}

    def get_query_execution(self, QueryExecutionId):
        self._lanzar_error("get_query_execution")
        estado = self._estado[QueryExecutionId]
        estadisticas = {
            "DataScannedInBytes": BYTES_POR_CONSULTA,
            "EngineExecutionTimeInMillis": 5,
            "TotalExecutionTimeInMillis": 7,
        }
        if estado["colgada"] or estado["polls"] > 0:
            nombre = "RUNNING" if estado["visto"] else "QUEUED"
            estado["visto"] = True
            if not estado["colgada"]:
                estado["polls"] -= 1
            return {"QueryExecution": {"Status": {"State": nombre}, "Statistics": estadisticas}}
        if estado["falla"] is not None:
            return {"QueryExecution": {
                "Status": {
                    "State": "FAILED",
                    "StateChangeReason": "falla simulada",
                    "AthenaError": {"ErrorCategory": estado["falla"]["categoria"]},
                },
                "Statistics": estadisticas,
            }}
        return {"QueryExecution": {"Status": {"State": "SUCCEEDED"}, "Statistics": estadisticas}}

    def get_query_results(self, QueryExecutionId, NextToken=None):
        self._lanzar_error("get_query_results")
        filas = self._filas[QueryExecutionId]
        return {"ResultSet": {"Rows": [
            {"Data": [{"VarCharValue": v} if v is not None else {} for v in fila]} for fila in filas
        ]}}

    def stop_query_execution(self, QueryExecutionId):
        self.detenidas.append(QueryExecutionId)
        return {}

    def get_work_group(self, WorkGroup):
        return {"WorkGroup": {"Configuration": {"EnforceWorkGroupConfiguration": self.enforce}}}

    def _lanzar_error(self, operacion: str) -> None:
        pendientes = self._errores.get(operacion)
        if pendientes:
            raise ErrorCliente(pendientes.pop(0))

    def _consumir_costo(self, sql: str) -> float:
        total = 0.0
        for entrada in self._costos:
            if entrada["patron"] in sql and entrada["veces"] != 0:
                total += entrada["segundos"]
                if entrada["veces"] is not None:
                    entrada["veces"] -= 1
        return total

    @staticmethod
    def _buscar(entradas: list[dict], sql: str) -> dict | None:
        for entrada in entradas:
            if entrada["patron"] in sql and entrada["veces"] != 0:
                if entrada["veces"] is not None:
                    entrada["veces"] -= 1
                return entrada
        return None


def cuerpo_lock(estado: str, expira_s: float, run_id: str | None = None) -> bytes:
    instante = INSTANTE_BASE + timedelta(seconds=expira_s)
    return json.dumps({
        "estado": estado,
        "run_id": run_id,
        "ts_utc": formato_iso(INSTANTE_BASE),
        "expira_utc": formato_iso(instante),
    }).encode("utf-8")


def cuerpo_ultimo_run(run_id: str, tablas: dict | None = None) -> bytes:
    return json.dumps({
        "schema": 1,
        "run_id": run_id,
        "estado": "ok",
        "tablas": tablas or {},
    }).encode("utf-8")


def lineas_json(salida: str) -> list[dict]:
    return [json.loads(linea) for linea in salida.splitlines() if linea.startswith("{")]


def sentencias_etapa(clave: str) -> str:
    if clave == "14":
        alters = "".join(
            f"ALTER TABLE {tabla} SET LOCATION 's3://<bucket-maghsa-dwh>/analytics/runs/<run_id>/{tabla}/';\n"
            for tabla in TABLAS_VIVAS
            if tabla != HECHOS
        )
        return alters
    if clave == "14p":
        return f"ALTER TABLE {HECHOS} SET LOCATION 's3://<bucket-maghsa-dwh>/analytics/runs/<run_id>/{HECHOS}/';\n"
    if clave == "14r":
        return (
            f"DROP TABLE IF EXISTS {HECHOS};\n"
            f"CREATE EXTERNAL TABLE {HECHOS} (monto_total double) LOCATION '<location_hechos>';\n"
            f"MSCK REPAIR TABLE {HECHOS};\n"
        )
    if clave == "15":
        return "-- GATE: G15 ZERO\nSELECT 1 AS ctrl FROM g15_publicacion;\n"
    if clave == "99":
        return "DROP TABLE IF EXISTS tmp_etapa_01;\nDROP VIEW IF EXISTS tmp_v_compras;\n"
    if clave == "07b":
        return "CREATE TABLE tmp_etapa_07b AS SELECT 1 AS n;\n-- GATE: G1 ZERO\nSELECT 1 AS ctrl FROM g1_duplicados;\n"
    if clave == "07c":
        return "CREATE TABLE tmp_a_hechos_07c AS SELECT 1 AS n;\n"
    if clave == "07d":
        return "INSERT INTO tmp_a_hechos SELECT 1 AS n;\n"
    if clave == "13":
        return (
            "-- GATE: G2.fk ZERO\nSELECT 1 AS ctrl FROM g2_fk;\n"
            "-- GATE: G2.conteo ZERO\nSELECT 1 AS ctrl FROM g2_conteo;\n"
            "-- GATE: G2.tiempo ZERO\nSELECT 1 AS ctrl FROM g2_tiempo;\n"
            "-- GATE: G2.rango ZERO\nSELECT 1 AS ctrl FROM g2_rango;\n"
            "-- GATE: G3 ZERO_FORZABLE\nSELECT 1 AS ctrl FROM g3_nuevo;\n"
        )
    return f"CREATE TABLE tmp_etapa_{clave} AS SELECT 1 AS n;\n"


def escribir_sql_sintetico(directorio: Path) -> Path:
    directorio.mkdir(parents=True, exist_ok=True)
    for clave, nombre in ARCHIVOS_SINTETICOS.items():
        (directorio / nombre).write_text(sentencias_etapa(clave), encoding="utf-8")
    (directorio / "orden.txt").write_text("\n".join(ORDEN_SINTETICO) + "\n", encoding="utf-8")
    return directorio


@pytest.fixture
def eventos() -> list:
    return []


@pytest.fixture
def reloj() -> FakeReloj:
    return FakeReloj()


@pytest.fixture
def glue() -> FakeGlue:
    fake = FakeGlue()
    fake.sembrar_legado()
    return fake


@pytest.fixture
def s3(eventos) -> FakeS3:
    return FakeS3(eventos)


@pytest.fixture
def athena(glue, reloj, eventos) -> FakeAthena:
    return FakeAthena(glue, reloj, eventos)


@pytest.fixture
def sql_dir(tmp_path) -> Path:
    return escribir_sql_sintetico(tmp_path / "sql")


@pytest.fixture
def deps(athena, s3, glue, reloj, sql_dir) -> Dependencias:
    config = Config(bucket=BUCKET, base=BASE_GLUE, workgroup="primary", sql_dir=sql_dir)
    return Dependencias(athena=athena, s3=s3, glue=glue, reloj=reloj, config=config)
