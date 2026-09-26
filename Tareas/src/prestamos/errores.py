"""Jerarquia de errores del dominio.

Toda operacion invalida levanta una subclase de ErrorDominio. La capa de
linea de comando solo atrapa ErrorDominio y muestra el mensaje al usuario;
cualquier otra excepcion se considera un defecto y se reporta a Sentry.
"""


class ErrorDominio(Exception):
    """Error esperado del negocio, seguro de mostrar al usuario final."""


class ErrorAutenticacion(ErrorDominio):
    """Credenciales invalidas o sesion inexistente."""


class ErrorPermiso(ErrorDominio):
    """El rol de la sesion no autoriza la operacion solicitada."""


class ErrorValidacion(ErrorDominio):
    """Entrada mal formada: RUT invalido, fecha imposible, campo vacio."""


class ErrorNoEncontrado(ErrorDominio):
    """La entidad referida no existe en la persistencia."""


class ErrorDuplicado(ErrorDominio):
    """Ya existe una entidad con el mismo identificador natural."""


class ErrorReglaNegocio(ErrorDominio):
    """La operacion es sintacticamente valida pero viola una regla del negocio."""


class ErrorTransicion(ErrorReglaNegocio):
    """La transicion de estado pedida no esta permitida para el estado actual."""


class ErrorDisponibilidad(ErrorReglaNegocio):
    """El equipo no esta disponible en el rango de fechas pedido."""
