"""Maquina de estados de una solicitud de prestamo.

Es el corazon del sistema: toda operacion que cambia el estado de una
solicitud pasa por transicionar(), de modo que no existe ningun camino en el
codigo capaz de saltarse la tabla de transiciones.

Diagrama (ver docs/estados-y-transiciones.md):

    POR_REVISAR --aprobar--> APROBADA --entregar--> EN_PRESTAMO
         |                       |                      |
      rechazar                cancelar             (vence plazo)
         v                       v                      v
     RECHAZADA              CANCELADA           PERIODO_GRACIA
                                                   |    |    |
                                          renovar  |    |    | (vence gracia)
                                    EN_PRESTAMO <--+    |    +--> ATRASADA
                                                        v              |
                                                    CONCLUIDA <--------+
"""

from .errores import ErrorPermiso, ErrorTransicion
from .reglas import ROL_ENCARGADO, ROL_SOLICITANTE

POR_REVISAR = "por_revisar"
APROBADA = "aprobada"
RECHAZADA = "rechazada"
EN_PRESTAMO = "en_prestamo"
PERIODO_GRACIA = "periodo_gracia"
ATRASADA = "atrasada"
CONCLUIDA = "concluida"
CANCELADA = "cancelada"

SISTEMA = "sistema"

ESTADOS = (
    POR_REVISAR,
    APROBADA,
    RECHAZADA,
    EN_PRESTAMO,
    PERIODO_GRACIA,
    ATRASADA,
    CONCLUIDA,
    CANCELADA,
)

# Estados en los que la solicitud sigue viva y por lo tanto ocupa el equipo.
ESTADOS_ACTIVOS = (POR_REVISAR, APROBADA, EN_PRESTAMO, PERIODO_GRACIA, ATRASADA)

# Estados en los que el equipo ya esta fisicamente en poder del solicitante.
ESTADOS_EN_PODER = (EN_PRESTAMO, PERIODO_GRACIA, ATRASADA)

ESTADOS_FINALES = (RECHAZADA, CONCLUIDA, CANCELADA)

# (estado_origen, accion) -> (estado_destino, roles autorizados)
TRANSICIONES: dict[tuple[str, str], tuple[str, tuple[str, ...]]] = {
    (POR_REVISAR, "aprobar"): (APROBADA, (ROL_ENCARGADO,)),
    (POR_REVISAR, "rechazar"): (RECHAZADA, (ROL_ENCARGADO,)),
    (POR_REVISAR, "cancelar"): (CANCELADA, (ROL_SOLICITANTE, ROL_ENCARGADO)),
    (APROBADA, "entregar"): (EN_PRESTAMO, (ROL_ENCARGADO,)),
    (APROBADA, "cancelar"): (CANCELADA, (ROL_SOLICITANTE, ROL_ENCARGADO, SISTEMA)),
    (EN_PRESTAMO, "vencer"): (PERIODO_GRACIA, (SISTEMA,)),
    (EN_PRESTAMO, "concluir"): (CONCLUIDA, (ROL_ENCARGADO,)),
    (PERIODO_GRACIA, "renovar"): (EN_PRESTAMO, (ROL_SOLICITANTE, ROL_ENCARGADO)),
    (PERIODO_GRACIA, "concluir"): (CONCLUIDA, (ROL_ENCARGADO,)),
    (PERIODO_GRACIA, "atrasar"): (ATRASADA, (SISTEMA,)),
    (ATRASADA, "concluir"): (CONCLUIDA, (ROL_ENCARGADO,)),
}


def acciones_posibles(estado: str) -> list[str]:
    return [accion for (origen, accion) in TRANSICIONES if origen == estado]


def es_activo(estado: str) -> bool:
    return estado in ESTADOS_ACTIVOS


def transicionar(estado_actual: str, accion: str, rol: str) -> str:
    """Devuelve el estado resultante o levanta un error del dominio.

    Se separan dos fallas distintas a proposito: una transicion inexistente
    (ErrorTransicion) y una transicion que existe pero no corresponde al rol
    (ErrorPermiso). Las pruebas negativas distinguen ambos casos.
    """
    if estado_actual not in ESTADOS:
        raise ErrorTransicion(f"Estado desconocido: {estado_actual}")

    destino = TRANSICIONES.get((estado_actual, accion))
    if destino is None:
        posibles = ", ".join(acciones_posibles(estado_actual)) or "ninguna"
        raise ErrorTransicion(
            f"No se puede '{accion}' una solicitud en estado '{estado_actual}'. "
            f"Acciones permitidas: {posibles}"
        )

    estado_destino, roles = destino
    if rol not in roles:
        raise ErrorPermiso(
            f"El rol '{rol}' no puede ejecutar '{accion}' sobre una solicitud "
            f"en estado '{estado_actual}'"
        )
    return estado_destino
