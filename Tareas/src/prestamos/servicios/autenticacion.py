"""RF01 - Inicio de sesion.

Implementacion de referencia: sirve de patron para el resto de los servicios.
El flujo es siempre el mismo, validar entrada, consultar el almacen, aplicar
la regla, registrar el evento y devolver un objeto de dominio.

Criterio de aceptacion RF01: con correo y contrasena correctos se obtiene una
sesion con el rol correspondiente; con credenciales incorrectas se levanta
ErrorAutenticacion y el mensaje no revela si fallo el correo o la contrasena.
"""

from .. import almacen, registro, seguridad, validaciones
from ..errores import ErrorAutenticacion
from ..reglas import ROL_ENCARGADO, ROL_SOLICITANTE
from ..sesion import Sesion

_MENSAJE_GENERICO = "Correo o contrasena incorrectos"


def iniciar_sesion(correo: str, contrasena: str) -> Sesion:
    """Autentica contra encargados y solicitantes y devuelve una Sesion.

    Las cuentas son separadas por decision de equipo: un mismo correo no
    puede ser encargado y solicitante a la vez, asi que basta con buscar en
    una coleccion y luego en la otra.
    """
    try:
        correo_normalizado = validaciones.correo(correo)
    except Exception:
        # Un correo mal formado se trata como credencial incorrecta para no
        # entregar informacion util a quien intenta adivinar cuentas.
        registro.evento("login_fallido", "Correo con formato invalido", actor=str(correo), nivel="WARNING")
        raise ErrorAutenticacion(_MENSAJE_GENERICO)

    if not contrasena:
        registro.evento("login_fallido", "Contrasena vacia", actor=correo_normalizado, nivel="WARNING")
        raise ErrorAutenticacion(_MENSAJE_GENERICO)

    encargado = almacen.buscar("encargados", "correo", correo_normalizado)
    if encargado and seguridad.verificar(contrasena, encargado.get("contrasena_hash", "")):
        registro.evento("login_exitoso", "Ingreso de encargado", actor=encargado["id"])
        return Sesion(
            rol=ROL_ENCARGADO,
            identificador=encargado["id"],
            nombre=encargado["nombre"],
            correo=encargado["correo"],
        )

    solicitante = almacen.buscar("solicitantes", "correo", correo_normalizado)
    if solicitante and seguridad.verificar(contrasena, solicitante.get("contrasena_hash", "")):
        registro.evento("login_exitoso", "Ingreso de solicitante", actor=solicitante["rut"])
        return Sesion(
            rol=ROL_SOLICITANTE,
            identificador=solicitante["rut"],
            nombre=solicitante["nombre"],
            correo=solicitante["correo"],
        )

    registro.evento("login_fallido", "Credenciales incorrectas", actor=correo_normalizado, nivel="WARNING")
    raise ErrorAutenticacion(_MENSAJE_GENERICO)


def cerrar_sesion(sesion: Sesion | None) -> None:
    if sesion is not None:
        registro.evento("logout", "Cierre de sesion", actor=sesion.identificador)
