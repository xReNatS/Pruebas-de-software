"""Sesion de usuario en memoria.

No hay tokens ni expiracion: la sesion vive mientras dura el proceso de la
linea de comando. Se pasa explicitamente a cada servicio para que las
comprobaciones de permiso sean visibles en la firma de cada funcion.
"""

from dataclasses import dataclass

from .errores import ErrorPermiso
from .reglas import ROL_ENCARGADO, ROL_SOLICITANTE


@dataclass(frozen=True)
class Sesion:
    rol: str
    identificador: str  # RUT si es solicitante, id si es encargado
    nombre: str
    correo: str

    @property
    def es_encargado(self) -> bool:
        return self.rol == ROL_ENCARGADO

    @property
    def es_solicitante(self) -> bool:
        return self.rol == ROL_SOLICITANTE

    def exigir_rol(self, rol: str) -> None:
        if self.rol != rol:
            raise ErrorPermiso(
                f"Esta operacion requiere el rol '{rol}' y la sesion es '{self.rol}'"
            )

    def exigir_encargado(self) -> None:
        self.exigir_rol(ROL_ENCARGADO)

    def exigir_solicitante(self) -> None:
        self.exigir_rol(ROL_SOLICITANTE)
