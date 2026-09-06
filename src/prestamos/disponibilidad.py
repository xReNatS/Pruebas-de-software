"""Calculo de disponibilidad de equipos.

Regla adoptada por el equipo: un equipo queda bloqueado desde el momento en
que alguien lo pide y mientras la solicitud siga activa, sin importar si esta
por revisar, aprobada, en prestamo, en periodo de gracia o atrasada. La razon
es que un prestamo puede extenderse, de modo que no se garantiza que el equipo
se desocupe en una fecha futura. Esto tambien resuelve la carrera entre dos
personas que piden el mismo equipo: gana quien registra primero.
"""

from datetime import date

from . import almacen
from .estados import ESTADOS_ACTIVOS

EQUIPO_DISPONIBLE = "disponible"
EQUIPO_EN_USO = "en_uso"
EQUIPO_FUERA_SERVICIO = "fuera_de_servicio"


def solicitudes_activas() -> list[dict]:
    return [s for s in almacen.leer("solicitudes") if s.get("estado") in ESTADOS_ACTIVOS]


def bloqueos_por_equipo() -> dict[str, list[dict]]:
    """Codigo de equipo -> solicitudes activas que lo tienen tomado."""
    bloqueos: dict[str, list[dict]] = {}
    for solicitud in solicitudes_activas():
        for codigo in solicitud.get("equipos", []):
            bloqueos.setdefault(codigo, []).append(solicitud)
    return bloqueos


def esta_bloqueado(codigo: str, bloqueos: dict[str, list[dict]] | None = None) -> bool:
    tabla = bloqueos_por_equipo() if bloqueos is None else bloqueos
    return bool(tabla.get(codigo))


def esta_disponible(equipo: dict, bloqueos: dict[str, list[dict]] | None = None) -> bool:
    """Un equipo esta disponible si no esta fuera de servicio ni bloqueado."""
    if equipo.get("estado") == EQUIPO_FUERA_SERVICIO:
        return False
    return not esta_bloqueado(equipo["codigo"], bloqueos)


def equipos_disponibles() -> list[dict]:
    bloqueos = bloqueos_por_equipo()
    return [e for e in almacen.leer("equipos") if esta_disponible(e, bloqueos)]


def estado_calculado(equipo: dict, bloqueos: dict[str, list[dict]] | None = None) -> str:
    """Estado mostrado al usuario, derivado de las solicitudes activas.

    El estado del equipo no se guarda duplicado en el JSON salvo
    'fuera_de_servicio', que si es una decision manual del encargado.
    """
    if equipo.get("estado") == EQUIPO_FUERA_SERVICIO:
        return EQUIPO_FUERA_SERVICIO
    return EQUIPO_EN_USO if esta_bloqueado(equipo["codigo"], bloqueos) else EQUIPO_DISPONIBLE


def motivo_no_disponible(codigo: str) -> str | None:
    """Explicacion legible de por que un equipo no se puede pedir."""
    equipo = almacen.buscar("equipos", "codigo", codigo)
    if equipo is None:
        return f"El equipo {codigo} no existe"
    if equipo.get("estado") == EQUIPO_FUERA_SERVICIO:
        return f"El equipo {codigo} esta fuera de servicio"
    activas = bloqueos_por_equipo().get(codigo, [])
    if activas:
        solicitud = activas[0]
        return (
            f"El equipo {codigo} esta tomado por la solicitud {solicitud['id']} "
            f"(estado {solicitud['estado']}, hasta {solicitud.get('fecha_devolucion')})"
        )
    return None


def hay_traslape(inicio_a: date, fin_a: date, inicio_b: date, fin_b: date) -> bool:
    """Utilidad para pruebas de borde sobre rangos de fechas."""
    return inicio_a <= fin_b and inicio_b <= fin_a
