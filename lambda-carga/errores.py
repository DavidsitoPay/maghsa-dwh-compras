"""Errores de la carga: codigo estable para logs, reintentos y rollback."""

# AthenaError.ErrorCategory: 1 System, 2 User, 3 Other
CATEGORIA_ERROR_SISTEMA = 1


class CargaError(Exception):
    def __init__(self, codigo: str, reintentable: bool = False, motivo: str | None = None):
        super().__init__(codigo)
        self.codigo = codigo
        self.reintentable = reintentable
        self.motivo = motivo


def codigo_error(excepcion: BaseException) -> str | None:
    respuesta = getattr(excepcion, "response", None)
    if not isinstance(respuesta, dict):
        return None
    return respuesta.get("Error", {}).get("Code")
