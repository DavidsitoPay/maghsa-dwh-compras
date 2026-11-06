"""Lecturas del Glue Data Catalog: ubicacion vigente de cada tabla y runs referenciados."""

from estado_s3 import run_ids_en
from tablas import HECHOS


class CatalogoGlue:
    def __init__(self, glue, base: str):
        self._glue = glue
        self._base = base

    def ubicacion(self, tabla: str) -> str:
        return self._tabla(tabla)["StorageDescriptor"]["Location"]

    def hechos_modo(self) -> str:
        parametros = self._tabla(HECHOS).get("Parameters", {})
        return "proyeccion" if parametros.get("projection.enabled") == "true" else "recreate"

    def run_ids_referenciados(self) -> set[str]:
        ids: set[str] = set()
        for tabla in self._paginar(self._glue.get_tables, "TableList", DatabaseName=self._base):
            if tabla.get("TableType") == "VIRTUAL_VIEW":
                continue
            ids |= run_ids_en(tabla.get("StorageDescriptor", {}).get("Location", ""))
            particiones = self._paginar(
                self._glue.get_partitions,
                "Partitions",
                DatabaseName=self._base,
                TableName=tabla["Name"],
            )
            for particion in particiones:
                ids |= run_ids_en(particion.get("StorageDescriptor", {}).get("Location", ""))
        return ids

    def _tabla(self, tabla: str) -> dict:
        return self._glue.get_table(DatabaseName=self._base, Name=tabla)["Table"]

    def _paginar(self, metodo, clave: str, **argumentos) -> list:
        resultado: list = []
        siguiente = None
        while True:
            extra = {"NextToken": siguiente} if siguiente else {}
            respuesta = metodo(**argumentos, **extra)
            resultado.extend(respuesta[clave])
            siguiente = respuesta.get("NextToken")
            if not siguiente:
                return resultado
