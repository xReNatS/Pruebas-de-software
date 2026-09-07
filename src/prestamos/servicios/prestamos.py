"""RF08 - Registrar devolucion (encargado), RF10 - Realizar devolucion
(solicitante) y RF11 - Renovar el prestamo. Incluye la entrega y las
transiciones automaticas por fecha.

Responsable: integrante B. Estado: pendiente de implementacion.

Modelado de la devolucion, decision del equipo: RF10 y RF08 son los dos lados
del mismo hecho fisico. El solicitante declara la devolucion (RF10), lo que
solo escribe la marca devolucion_declarada_en; el equipo queda liberado
unicamente cuando el encargado confirma la recepcion (RF08) y la solicitud
pasa a 'concluida'. Asi la maquina de estados no necesita un estado extra.

Contrato esperado y criterios de aceptacion:

RF08.1 Solo un encargado confirma devoluciones.
RF08.2 Se puede concluir desde 'en_prestamo', 'periodo_gracia' y 'atrasada';
       desde cualquier otro estado se levanta ErrorTransicion.
RF08.3 Al concluir desde 'atrasada' el solicitante queda en estado 'pendiente'.
RF08.4 Al concluir, los equipos vuelven a estar disponibles.
RF08.5 La confirmacion queda registrada en el log con el actor encargado.

RF10.1 Solo el dueno de la solicitud puede declarar su devolucion.
RF10.2 Se permite declarar antes del vencimiento (devolucion anticipada).
RF10.3 Declarar no libera el equipo por si solo; hasta que RF08 confirme, la
       solicitud sigue activa y el equipo sigue bloqueado.

RF11.1 Solo se renueva estando en 'periodo_gracia'.
RF11.2 Como maximo reglas.MAX_RENOVACIONES renovacion, de hasta
       reglas.DIAS_MAX_RENOVACION dias; una segunda intentona levanta
       ErrorReglaNegocio.
RF11.3 Al renovar, la solicitud vuelve a 'en_prestamo' con nueva fecha de
       devolucion y el contador de renovaciones sube en uno.

Transiciones automaticas (ejecutadas por el sistema, no por una persona):
  en_prestamo    -> periodo_gracia  al pasar la fecha de devolucion
  periodo_gracia -> atrasada        al pasar reglas.DIAS_PERIODO_GRACIA
  aprobada       -> cancelada       si no se retira en reglas.DIAS_PARA_RETIRO
"""

from datetime import date, timedelta

from .. import almacen, estados, modelos, registro, reglas
from ..errores import ErrorPermiso, ErrorReglaNegocio, ErrorValidacion
from ..sesion import Sesion
from . import personas


def registrar_entrega(sesion: Sesion, identificador: str) -> dict:
    """RF08.1: solo un encargado entrega fisicamente los equipos.

    La solicitud debe estar en 'aprobada' y pasa a 'en_prestamo'.
    El encargado toma posesión de los equipos y el solicitante ya
    no puede cancelar por su cuenta.
    """
    if not sesion.es_encargado:
        raise ErrorPermiso(
            f"Esta operacion requiere el rol 'encargado' y la sesion es '{sesion.rol}'"
        )

    solicitud = almacen.obtener("solicitudes", "id", identificador)
    nuevo_estado = estados.transicionar(solicitud["estado"], "entregar", sesion.rol)
    modelos.registrar_cambio(solicitud, nuevo_estado, sesion.identificador)
    almacen.reemplazar("solicitudes", "id", identificador, solicitud)
    registro.evento(
        "entrega_registrada",
        f"Solicitud {identificador} entregada al solicitante",
        actor=sesion.identificador,
    )
    return solicitud


def confirmar_devolucion(sesion: Sesion, identificador: str, observacion: str = "") -> dict:
    """RF08: confirma la recepcion de los equipos y la solicitud pasa a 'concluida'.

    Se puede concluir desde 'en_prestamo', 'periodo_gracia' o
    'atrasada' (RF08.2). Al cerrar, los equipos vuelven a estar
    disponibles (RF08.4). El actor encargado queda registrado en el log
    (RF08.5).
    """
    if not sesion.es_encargado:
        raise ErrorPermiso(
            f"Esta operacion requiere el rol 'encargado' y la sesion es '{sesion.rol}'"
        )

    solicitud = almacen.obtener("solicitudes", "id", identificador)
    venia_atrasada = solicitud["estado"] == estados.ATRASADA

    nuevo_estado = estados.transicionar(solicitud["estado"], "concluir", sesion.rol)
    modelos.registrar_cambio(solicitud, nuevo_estado, sesion.identificador, observacion)
    almacen.reemplazar("solicitudes", "id", identificador, solicitud)

    observacion_limpia = (observacion or "").strip()
    registro.evento(
        "devolucion_confirmada",
        f"Solicitud {identificador} concluida por el encargado"
        + (f". Observacion: {observacion_limpia}" if observacion_limpia else ""),
        actor=sesion.identificador,
    )

    # RF08.4 / RN11: devolver no borra el atraso. Quien no devolvio a tiempo
    # queda en estado 'pendiente' y no puede pedir de nuevo hasta que un
    # encargado lo reactive a mano. Lo marca el sistema y no el encargado que
    # recibe el equipo, porque no es una decision suya sino la regla.
    if venia_atrasada:
        personas.marcar_estado_por_sistema(
            solicitud["rut_solicitante"], reglas.SOLICITANTE_PENDIENTE
        )

    return solicitud


def declarar_devolucion(sesion: Sesion, identificador: str) -> dict:
    """RF10: el dueno declara la devolucion de los equipos.

    RF10.1: solo el dueño. RF10.2: se permite anticipada. RF10.3: no libera
    el equipo ni cambia el estado; solo marca devolucion_declarada_en.
    """
    solicitud = almacen.obtener("solicitudes", "id", identificador)

    if solicitud.get("rut_solicitante") != sesion.identificador:
        raise ErrorPermiso("Solo puede declarar la devolucion de sus propias solicitudes")

    fecha_actual = date.today().isoformat()
    solicitud["devolucion_declarada_en"] = fecha_actual
    modelos.registrar_cambio(solicitud, solicitud["estado"], sesion.identificador)
    almacen.reemplazar("solicitudes", "id", identificador, solicitud)
    registro.evento(
        "devolucion_declarada",
        f"Solicitud {identificador} con devolucion declarada para {fecha_actual}",
        actor=sesion.identificador,
    )
    return solicitud


def renovar_prestamo(sesion: Sesion, identificador: str, dias: int) -> dict:
    """RF11: renueva un prestamo en periodo de gracia.

    RF11.1: solo desde 'periodo_gracia'. RF11.2: maximo
    reglas.MAX_RENOVACIONES veces (1) y hasta reglas.DIAS_MAX_RENOVACION dias.
    RF11.3: vuelve a 'en_prestamo' con nueva fecha de devolucion y contador
    de renovaciones incrementado.
    """
    solicitud = almacen.obtener("solicitudes", "id", identificador)

    if solicitud.get("rut_solicitante") != sesion.identificador:
        raise ErrorPermiso("Solo puede renovar sus propios prestamos")

    estado_actual = solicitud["estado"]
    nuevo_estado = estados.transicionar(estado_actual, "renovar", sesion.rol)

    if dias > reglas.DIAS_MAX_RENOVACION:
        raise ErrorReglaNegocio(
            f"La renovacion no puede superar {reglas.DIAS_MAX_RENOVACION} dias (recibi {dias})"
        )

    renovaciones = solicitud.get("renovaciones", 0)
    if renovaciones >= reglas.MAX_RENOVACIONES:
        raise ErrorReglaNegocio("Ya se realizo la unica renovacion permitida")

    # Nueva fecha de devolucion: fecha actual + dias
    fecha_devolucion = (date.today() + timedelta(days=dias)).isoformat()
    solicitud["fecha_devolucion"] = fecha_devolucion
    solicitud["renovaciones"] = renovaciones + 1

    modelos.registrar_cambio(solicitud, nuevo_estado, sesion.identificador)
    almacen.reemplazar("solicitudes", "id", identificador, solicitud)
    registro.evento(
        "prestamo_renovado",
        f"Solicitud {identificador} renovada por {dias} dias (total renovaciones: {solicitud['renovaciones']})",
        actor=sesion.identificador,
    )
    return solicitud


def actualizar_estados_por_fecha(hoy: date | None = None) -> list[dict]:
    """Aplica transiciones automaticas por fecha y devuelve solicitudes tocadas.

    - en_prestamo -> periodo_gracia al pasar fecha_devolucion
    - periodo_gracia -> atrasada al pasar DIAS_PERIODO_GRACIA
    - aprobada -> cancelada si no se retira en DIAS_PARA_RETIRO
    """
    if hoy is None:
        hoy = date.today()

    solicitudes = almacen.leer("solicitudes")
    tocadas: list[dict] = []

    for solicitud in solicitudes:
        estado = solicitud.get("estado")
        fecha_devolucion_str = solicitud.get("fecha_devolucion")
        fecha_retiro_str = solicitud.get("fecha_retiro")
        if not fecha_devolucion_str or not fecha_retiro_str:
            continue

        fecha_devolucion = date.fromisoformat(fecha_devolucion_str)
        fecha_retiro = date.fromisoformat(fecha_retiro_str)

        if estado == estados.EN_PRESTAMO and hoy > fecha_devolucion:
            nuevo_estado = estados.transicionar(estado, "vencer", estados.SISTEMA)
            modelos.registrar_cambio(solicitud, nuevo_estado, estados.SISTEMA)
            tocadas.append(solicitud)

        elif estado == estados.PERIODO_GRACIA:
            fin_gracia = fecha_devolucion + timedelta(days=reglas.DIAS_PERIODO_GRACIA)
            if hoy > fin_gracia:
                nuevo_estado = estados.transicionar(estado, "atrasar", estados.SISTEMA)
                modelos.registrar_cambio(solicitud, nuevo_estado, estados.SISTEMA)
                # RF08.3: solicitante queda pendiente al atrasarse
                solicitante = almacen.obtener("solicitantes", "rut", solicitud["rut_solicitante"])
                solicitante["estado"] = reglas.SOLICITANTE_PENDIENTE
                almacen.reemplazar("solicitantes", "rut", solicitud["rut_solicitante"], solicitante)
                tocadas.append(solicitud)

        elif estado == estados.APROBADA:
            fin_retiro = fecha_retiro + timedelta(days=reglas.DIAS_PARA_RETIRO)
            if hoy > fin_retiro:
                nuevo_estado = estados.transicionar(estado, "cancelar", estados.SISTEMA)
                modelos.registrar_cambio(solicitud, nuevo_estado, estados.SISTEMA)
                tocadas.append(solicitud)

    if tocadas:
        almacen.escribir("solicitudes", solicitudes)

    return tocadas
