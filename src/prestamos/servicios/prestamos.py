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
from ..errores import (
    ErrorPermiso,
    ErrorReglaNegocio,
    ErrorTransicion,
    ErrorValidacion,
)
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

    # RF10.5: solo tiene sentido declarar lo que se tiene en la mano. Sin esta
    # comprobacion se podia declarar la devolucion de una solicitud rechazada
    # o cancelada, es decir de equipos que nunca salieron del laboratorio.
    if solicitud["estado"] not in estados.ESTADOS_EN_PODER:
        raise ErrorTransicion(
            f"No se puede declarar la devolucion de una solicitud en estado "
            f"'{solicitud['estado']}'. Solo se declara lo que ya se retiro: "
            f"{', '.join(estados.ESTADOS_EN_PODER)}"
        )

    # RF10.4: declarar dos veces no mueve la fecha original ni ensucia el
    # historial. Lo que vale es cuando el solicitante dijo por primera vez que
    # devolvia, porque es la fecha que el encargado va a contrastar.
    if solicitud.get("devolucion_declarada_en"):
        return solicitud

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

    if not 1 <= dias <= reglas.DIAS_MAX_RENOVACION:
        raise ErrorValidacion(
            f"La renovacion debe ser de entre 1 y {reglas.DIAS_MAX_RENOVACION} dias "
            f"(recibi {dias})"
        )

    renovaciones = solicitud.get("renovaciones", 0)
    if renovaciones >= reglas.MAX_RENOVACIONES:
        raise ErrorReglaNegocio("Ya se realizo la unica renovacion permitida")

    # RF11.5: la extension cuenta desde la fecha de devolucion original, no
    # desde hoy. Como solo se renueva en periodo de gracia, hoy siempre es
    # posterior al vencimiento: calcular desde hoy regalaria dias, y mientras
    # mas se demorase el solicitante en renovar, mas dias ganaria.
    devolucion_original = date.fromisoformat(solicitud["fecha_devolucion"])
    solicitud["fecha_devolucion"] = (devolucion_original + timedelta(days=dias)).isoformat()
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
    """Aplica las transiciones automaticas por fecha. Rol: sistema.

    AUT.1  en_prestamo    -> periodo_gracia  al pasar la fecha de devolucion
    AUT.2  periodo_gracia -> atrasada        al pasar el dia de gracia
    AUT.3  al marcar un atraso, el solicitante queda 'pendiente' (RN11)
    AUT.4  aprobada       -> cancelada       si no se retira a tiempo
    AUT.5  acepta una fecha explicita, para poder probar el paso del tiempo
    AUT.6  es idempotente: la segunda corrida del mismo dia no cambia nada
    AUT.7  cada cambio queda en el log con actor 'sistema'

    Las transiciones se encadenan dentro de la misma corrida. Un prestamo
    vencido hace tres semanas tiene que quedar 'atrasada' de inmediato: si
    cada corrida avanzara un solo paso, al abrir la aplicacion quedaria en
    'periodo_gracia' y le regalaria un dia de gracia que vencio hace mucho.
    """
    hoy = hoy or date.today()
    solicitudes = almacen.leer("solicitudes")
    tocadas: list[dict] = []

    for solicitud in solicitudes:
        if _avanzar_por_fecha(solicitud, hoy):
            tocadas.append(solicitud)

    if tocadas:
        almacen.escribir("solicitudes", solicitudes)

    return tocadas


def _avanzar_por_fecha(solicitud: dict, hoy: date) -> bool:
    """Aplica todas las transiciones que correspondan. Devuelve si cambio algo."""
    cambio = False

    # El bucle deja la solicitud en su estado final para la fecha dada, en vez
    # de avanzar un paso por corrida.
    while True:
        siguiente = _siguiente_transicion(solicitud, hoy)
        if siguiente is None:
            return cambio

        accion, motivo = siguiente
        estado_anterior = solicitud["estado"]
        nuevo_estado = estados.transicionar(estado_anterior, accion, estados.SISTEMA)
        modelos.registrar_cambio(solicitud, nuevo_estado, estados.SISTEMA, motivo)
        cambio = True

        registro.evento(
            "transicion_automatica",
            f"Solicitud {solicitud['id']} paso de '{estado_anterior}' a "
            f"'{nuevo_estado}': {motivo}",
            actor=estados.SISTEMA,
            nivel="WARNING" if nuevo_estado == estados.ATRASADA else "INFO",
        )

        # RN11: el atraso deja al solicitante sin poder pedir hasta que un
        # encargado lo reactive. marcar_estado_por_sistema deja su propio
        # evento en el log, con el mismo actor.
        if nuevo_estado == estados.ATRASADA:
            personas.marcar_estado_por_sistema(
                solicitud["rut_solicitante"], reglas.SOLICITANTE_PENDIENTE
            )


def _siguiente_transicion(solicitud: dict, hoy: date) -> tuple[str, str] | None:
    """Que corresponde hacerle a esta solicitud hoy, si es que algo."""
    estado = solicitud.get("estado")

    if estado == estados.EN_PRESTAMO:
        devolucion = _fecha(solicitud, "fecha_devolucion")
        if devolucion and hoy > devolucion:
            return "vencer", f"vencio el plazo de devolucion ({devolucion.isoformat()})"

    elif estado == estados.PERIODO_GRACIA:
        devolucion = _fecha(solicitud, "fecha_devolucion")
        if devolucion and hoy > devolucion + timedelta(days=reglas.DIAS_PERIODO_GRACIA):
            return "atrasar", (
                f"vencio el periodo de gracia de {reglas.DIAS_PERIODO_GRACIA} dia(s)"
            )

    elif estado == estados.APROBADA:
        # AUT.4: el plazo corre desde la aprobacion, que es cuando el
        # solicitante quedo habilitado para ir a buscar el equipo. Si el
        # historial no la tiene, se cae a la fecha de retiro.
        referencia = _fecha_de_aprobacion(solicitud) or _fecha(solicitud, "fecha_retiro")
        if referencia and hoy > referencia + timedelta(days=reglas.DIAS_PARA_RETIRO):
            return "cancelar", (
                f"no se retiro dentro de los {reglas.DIAS_PARA_RETIRO} dias posteriores "
                f"a la aprobacion"
            )

    return None


def _fecha(solicitud: dict, campo: str) -> date | None:
    valor = solicitud.get(campo)
    return date.fromisoformat(valor) if valor else None


def _fecha_de_aprobacion(solicitud: dict) -> date | None:
    """Fecha en que la solicitud fue aprobada, leida del historial."""
    for entrada in reversed(solicitud.get("historial", [])):
        if entrada.get("estado") == estados.APROBADA and entrada.get("en"):
            return date.fromisoformat(entrada["en"][:10])
    return None
