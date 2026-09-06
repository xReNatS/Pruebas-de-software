"""RF02 - Registrar persona autorizada (solicitantes y encargados).

Responsable: integrante A. Estado: pendiente de implementacion.

Contrato esperado y criterios de aceptacion:

RF02.1 Solo un encargado autenticado puede registrar personas. Con una sesion
       de solicitante debe levantarse ErrorPermiso.
RF02.2 El RUT y el correo son unicos. Un duplicado levanta ErrorDuplicado y no
       modifica el archivo JSON.
RF02.3 Un RUT con digito verificador incorrecto levanta ErrorValidacion.
RF02.4 La contrasena nunca se guarda en texto plano: el JSON solo contiene
       contrasena_hash.
RF02.5 Cada registro exitoso deja un evento en el log.

Puntos de apoyo ya construidos: modelos.nuevo_solicitante,
modelos.nuevo_encargado, almacen.agregar, almacen.buscar, sesion.exigir_encargado.
"""

from ..sesion import Sesion


def registrar_solicitante(
    sesion: Sesion, nombre: str, rut: str, correo: str, contrasena: str
) -> dict:
    raise NotImplementedError("RF02: registrar solicitante")


def registrar_encargado(sesion: Sesion, nombre: str, correo: str, contrasena: str) -> dict:
    raise NotImplementedError("RF02: registrar encargado")


def listar_solicitantes(sesion: Sesion) -> list[dict]:
    raise NotImplementedError("RF02: listar personas autorizadas")


def cambiar_estado_solicitante(sesion: Sesion, rut: str, estado: str) -> dict:
    """Pasa a 'pendiente' o devuelve a 'al_dia'. Lo usa tambien RF08."""
    raise NotImplementedError("RF02: cambiar estado de solicitante")
