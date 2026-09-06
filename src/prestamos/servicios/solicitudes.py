"""RF05 - Crear solicitud, RF06 - Consultar solicitudes,
RF07 - Aprobar/rechazar y RF09 - Cancelar solicitud.

Responsable: integrante B. Estado: pendiente de implementacion.

Contrato esperado y criterios de aceptacion:

RF05.1 Solo un solicitante crea solicitudes; un encargado recibe ErrorPermiso.
RF05.2 Una solicitud tiene 1 o 2 equipos (reglas.MIN/MAX_EQUIPOS_POR_SOLICITUD).
       Cero o tres equipos levantan ErrorValidacion.
RF05.3 Si son dos equipos, deben ser de categorias distintas
       (reglas.CATEGORIAS_DEBEN_SER_DISTINTAS), si no ErrorReglaNegocio.
RF05.4 Sumando lo que ya tiene en su poder, el solicitante no puede superar
       reglas.MAX_EQUIPOS_SIMULTANEOS.
RF05.5 Un solicitante en estado 'pendiente' no puede crear solicitudes.
RF05.6 La duracion no puede superar reglas.DIAS_MAX_PRESTAMO.
RF05.7 Un equipo tomado por otra solicitud activa levanta ErrorDisponibilidad
       con el motivo devuelto por disponibilidad.motivo_no_disponible.
RF05.8 La solicitud nace en estado 'por_revisar' y queda en el JSON.

RF06.1 Un solicitante ve unicamente sus propias solicitudes.
RF06.2 Un encargado ve todas y puede filtrar por vigentes, futuras y atrasadas.
RF06.3 El filtro de atrasadas se calcula por fecha, no por un campo escrito a mano.

RF07.1 Solo un encargado aprueba o rechaza, y solo sobre 'por_revisar'.
RF07.2 Aprobar sobre cualquier otro estado levanta ErrorTransicion.
RF07.3 Al aprobar se verifica de nuevo la disponibilidad: si el equipo se tomo
       entre la creacion y la aprobacion, la aprobacion falla con motivo.
RF07.4 El rechazo exige un motivo no vacio, que queda en el historial.

RF09.1 Un solicitante cancela solo sus propias solicitudes.
RF09.2 Solo se cancela en estado 'por_revisar' o 'aprobada'.
RF09.3 Al cancelar, los equipos vuelven a estar disponibles de inmediato.

Puntos de apoyo ya construidos: estados.transicionar, disponibilidad.*,
modelos.nueva_solicitud, modelos.registrar_cambio, almacen.siguiente_id.
"""

from datetime import date

from ..sesion import Sesion


def crear_solicitud(
    sesion: Sesion, codigos_equipos: list[str], fecha_retiro: date, fecha_devolucion: date
) -> dict:
    raise NotImplementedError("RF05: crear solicitud")


def listar_solicitudes(sesion: Sesion, filtro: str = "todas") -> list[dict]:
    """filtro: todas | vigentes | futuras | atrasadas | mias."""
    raise NotImplementedError("RF06: consultar solicitudes")


def detalle_solicitud(sesion: Sesion, identificador: str) -> dict:
    raise NotImplementedError("RF06: detalle de solicitud")


def aprobar_solicitud(sesion: Sesion, identificador: str) -> dict:
    raise NotImplementedError("RF07: aprobar solicitud")


def rechazar_solicitud(sesion: Sesion, identificador: str, motivo: str) -> dict:
    raise NotImplementedError("RF07: rechazar solicitud")


def cancelar_solicitud(sesion: Sesion, identificador: str, motivo: str = "") -> dict:
    raise NotImplementedError("RF09: cancelar solicitud")
