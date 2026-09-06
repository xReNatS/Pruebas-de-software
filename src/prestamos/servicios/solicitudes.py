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

from .. import almacen, disponibilidad, modelos, registro, validaciones
from .. import estados, reglas
from ..errores import (
    ErrorDisponibilidad,
    ErrorPermiso,
    ErrorReglaNegocio,
    ErrorValidacion,
)
from ..sesion import Sesion


def crear_solicitud(
    sesion: Sesion, codigos_equipos: list[str], fecha_retiro: date, fecha_devolucion: date
) -> dict:
    # RF05.1
    if sesion.es_encargado:
        raise ErrorPermiso(
            f"Esta operacion requiere el rol 'solicitante' y la sesion es '{sesion.rol}'"
        )

    # RF05.2
    codigos = [c.strip().upper() for c in codigos_equipos if c and c.strip()]
    if not (reglas.MIN_EQUIPOS_POR_SOLICITUD <= len(codigos) <= reglas.MAX_EQUIPOS_POR_SOLICITUD):
        raise ErrorValidacion(
            f"Una solicitud debe incluir entre {reglas.MIN_EQUIPOS_POR_SOLICITUD} "
            f"y {reglas.MAX_EQUIPOS_POR_SOLICITUD} equipos (recibi {len(codigos)})"
        )

    # RF05.6
    validaciones.rango_fechas(fecha_retiro, fecha_devolucion)
    duracion = (fecha_devolucion - fecha_retiro).days
    if duracion > reglas.DIAS_MAX_PRESTAMO:
        raise ErrorValidacion(
            f"La duracion maxima de un prestamo es de {reglas.DIAS_MAX_PRESTAMO} dias "
            f"(recibi {duracion})"
        )

    equipos: list[dict] = []
    for codigo in codigos:
        motivo = disponibilidad.motivo_no_disponible(codigo)
        if motivo is not None:
            raise ErrorDisponibilidad(motivo)
        equipo = almacen.buscar("equipos", "codigo", codigo)
        if equipo is None:  # defensa adicional, no deberia ocurrir
            raise ErrorDisponibilidad(f"El equipo {codigo} no existe")
        equipos.append(equipo)

    # RF05.3
    if len(equipos) == 2 and reglas.CATEGORIAS_DEBEN_SER_DISTINTAS:
        if equipos[0]["categoria"] == equipos[1]["categoria"]:
            raise ErrorReglaNegocio(
                f"Los dos equipos deben ser de categorias distintas "
                f"(ambos son '{equipos[0]['categoria']}')"
            )

    # RF05.7
    bloqueos = disponibilidad.bloqueos_por_equipo()
    for codigo in codigos:
        if disponibilidad.esta_bloqueado(codigo, bloqueos):
            motivo = disponibilidad.motivo_no_disponible(codigo) or (
                f"El equipo {codigo} no esta disponible"
            )
            raise ErrorDisponibilidad(motivo)

    # RF05.5
    persona = almacen.obtener("solicitantes", "rut", sesion.identificador)
    if persona["estado"] == reglas.SOLICITANTE_PENDIENTE:
        raise ErrorReglaNegocio(
            "El solicitante esta en estado 'pendiente' por un prestamo atrasado "
            "y no puede crear nuevas solicitudes"
        )

    # RF05.4
    en_poder = sum(
        len(s.get("equipos", []))
        for s in almacen.leer("solicitudes")
        if s.get("rut_solicitante") == sesion.identificador
        and s.get("estado") in estados.ESTADOS_EN_PODER
    )
    if en_poder + len(codigos) > reglas.MAX_EQUIPOS_SIMULTANEOS:
        raise ErrorReglaNegocio(
            f"El solicitante ya tiene {en_poder} equipo(s) en su poder y el maximo "
            f"simultaneo es {reglas.MAX_EQUIPOS_SIMULTANEOS}"
        )

    # RF05.8
    identificador = almacen.siguiente_id("solicitudes", "SOL")
    solicitud = modelos.nueva_solicitud(
        identificador, sesion.identificador, codigos, fecha_retiro, fecha_devolucion
    )
    almacen.agregar("solicitudes", solicitud)
    registro.evento(
        "solicitud_creada",
        f"Solicitud {identificador} con {len(codigos)} equipo(s)",
        actor=sesion.identificador,
    )
    return solicitud


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
