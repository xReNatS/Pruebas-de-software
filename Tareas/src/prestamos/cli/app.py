"""Punto de entrada de la aplicacion de linea de comando."""

from .. import registro
from ..errores import ErrorDominio
from ..servicios import autenticacion
from ..servicios import prestamos as srv_prestamos
from . import menu_encargado, menu_solicitante
from .comun import aviso, error, pedir, pedir_secreto, titulo

BANNER = "Sistema de prestamo de equipos - Laboratorio universitario"


def _actualizar_estados() -> None:
    """Aplica las transiciones automaticas por fecha al arrancar."""
    try:
        srv_prestamos.actualizar_estados_por_fecha()
    except NotImplementedError:
        pass
    except Exception as fallo:
        registro.excepcion("actualizacion_estados", fallo)


def ejecutar() -> int:
    titulo(BANNER)
    _actualizar_estados()

    while True:
        aviso("Ingrese sus credenciales (deje el correo vacio para salir)")
        correo = pedir("Correo", obligatorio=False)
        if not correo:
            aviso("Hasta luego")
            return 0
        clave = pedir_secreto("Contrasena")

        try:
            sesion = autenticacion.iniciar_sesion(correo, clave)
        except ErrorDominio as fallo:
            error(str(fallo))
            continue

        if sesion.es_encargado:
            menu_encargado.mostrar(sesion)
        else:
            menu_solicitante.mostrar(sesion)
        autenticacion.cerrar_sesion(sesion)
