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

    # No se reserva para un pasado que ya ocurrio. Una solicitud con fechas
    # vencidas nace atrasada, inmoviliza el equipo por un prestamo que nunca
    # va a suceder, y aparece en el listado de atrasadas del encargado como si
    # hubiera algo que reclamar. Se acepta el retiro de hoy mismo, que es el
    # caso normal de quien pasa a buscar el equipo en el momento. Hacia el
    # futuro no hay limite (supuesto A10).
    hoy = date.today()
    if fecha_retiro < hoy:
        raise ErrorValidacion(
            f"La fecha de retiro no puede ser anterior a hoy "
            f"(se pidio {fecha_retiro.isoformat()} y hoy es {hoy.isoformat()})"
        )

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
    if reglas.CATEGORIAS_DEBEN_SER_DISTINTAS:
        # Verificar categorias distintas entre los equipos del pedido actual y los ya comprometidos
        equipos_actuales = {e["categoria"] for e in equipos}

        # Obtener categorias de equipos ya comprometidos en solicitudes activas del mismo solicitante
        solicitudes_activas = disponibilidad.solicitudes_activas()
        equipos_comprometidos = set()
        for solicitud in solicitudes_activas:
            if solicitud.get("rut_solicitante") == sesion.identificador:
                for codigo in solicitud.get("equipos", []):
                    equipo = almacen.buscar("equipos", "codigo", codigo)
                    if equipo:
                        equipos_comprometidos.add(equipo["categoria"])

        # Verificar que no haya solapamiento de categorias
        if equipos_actuales & equipos_comprometidos:
            # Encontrar la categoria que se repite para el mensaje de error
            categoria_repetida = next(c for c in equipos_actuales if c in equipos_comprometidos)
            raise ErrorReglaNegocio(
                f"El solicitante ya tiene un equipo de la categoria '{categoria_repetida}' "
                f"en su poder y no puede solicitar otro equipo de la misma categoria"
            )

        # Verificar que dentro de la misma solicitud no haya dos equipos de la misma categoria
        if len(equipos) == 2 and len(equipos_actuales) < len(equipos):
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
        and s.get("estado") in estados.ESTADOS_ACTIVOS
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
    """filtro: todas | vigentes | futuras | atrasadas | mias.

    RF06.1: un solicitante ve unicamente sus propias solicitudes, salvo que
    pida explicitamente "mias" (el menu del solicitante siempre lo hace).
    RF06.2: un encargado ve todas y aplica el filtro que pidio.
    RF06.3: "atrasadas" se calcula por fecha contra hoy, no mirando un
    campo persistido, de modo que un atraso nuevo aparezca en el listado
    apenas ocurre, sin necesidad de reescribir la solicitud.
    """
    filtro_normalizado = (filtro or "todas").strip().lower()
    filtros_validos = {"todas", "vigentes", "futuras", "atrasadas", "mias"}
    if filtro_normalizado not in filtros_validos:
        raise ErrorValidacion(
            f"Filtro desconocido: {filtro!r}. Use uno de {sorted(filtros_validos)}"
        )

    solicitudes = almacen.leer("solicitudes")

    # RF06.1: el solicitante solo ve las suyas. "mias" lo pide el menu del
    # solicitante; cualquier otro filtro sobre un solicitante se restringe
    # igual, asi nadie ve lo ajeno por cambiar el nombre del filtro.
    if sesion.es_solicitante or filtro_normalizado == "mias":
        solicitudes = [s for s in solicitudes if s.get("rut_solicitante") == sesion.identificador]

    hoy = date.today()

    def _a_fecha(campo: str, solicitud: dict) -> date | None:
        valor = solicitud.get(campo)
        if not valor:
            return None
        return date.fromisoformat(valor)

    if filtro_normalizado == "todas" or filtro_normalizado == "mias":
        resultado = solicitudes
    elif filtro_normalizado == "vigentes":
        # La persona tiene el equipo en estos estados.
        resultado = [s for s in solicitudes if s.get("estado") in estados.ESTADOS_EN_PODER]
    elif filtro_normalizado == "futuras":
        # Aun no se entrego: la solicitud esta en cola (por_revisar o
        # aprobada) sin importar la fecha de retiro, porque si ya paso y
        # sigue sin entregar, sigue siendo "lo que viene".
        resultado = [
            s for s in solicitudes if s.get("estado") in (estados.POR_REVISAR, estados.APROBADA)
        ]
    else:  # atrasadas
        # Calculado por fecha (RF06.3): la solicitud sigue activa pero su
        # fecha de devolucion ya vencio, o el sistema la marco atrasada.
        resultado = []
        for s in solicitudes:
            if s.get("estado") == estados.ATRASADA:
                resultado.append(s)
                continue
            if s.get("estado") not in estados.ESTADOS_ACTIVOS:
                continue
            devolucion = _a_fecha("fecha_devolucion", s)
            if devolucion is not None and devolucion < hoy:
                resultado.append(s)

    # Orden estable: por id para que la presentacion en tabla no salte.
    return sorted(resultado, key=lambda s: s.get("id", ""))



def detalle_solicitud(sesion: Sesion, identificador: str) -> dict:
    """RF06: devuelve una solicitud puntual.

    Un solicitante solo puede ver el detalle de las suyas; un encargado
    puede ver cualquiera. La regla de visibilidad es la misma que en
    listar_solicitudes, simplemente aplicada a un unico registro.
    """
    solicitud = almacen.obtener("solicitudes", "id", identificador)
    if sesion.es_solicitante and solicitud.get("rut_solicitante") != sesion.identificador:
        raise ErrorPermiso("Solo puede ver el detalle de sus propias solicitudes")
    return solicitud


def aprobar_solicitud(sesion: Sesion, identificador: str) -> dict:
    """RF07.1 / RF07.2 / RF07.3: encarga pasa 'por_revisar' a 'aprobada'.

    La maquina de estados se delega a estados.transicionar, que se encarga
    de validar el origen y el rol. Antes de persistir se vuelve a chequear
    la disponibilidad de los equipos pedidos (RF07.3), porque entre que la
    solicitud se creo y se revisa otro pedido puede haber tomado el mismo
    equipo: la transicion automatica del estado no nos protege de eso.
    """
    if not sesion.es_encargado:
        raise ErrorPermiso(
            f"Esta operacion requiere el rol 'encargado' y la sesion es '{sesion.rol}'"
        )

    solicitud = almacen.obtener("solicitudes", "id", identificador)
    nuevo_estado = estados.transicionar(solicitud["estado"], "aprobar", sesion.rol)

    # RF07.3: revalidar disponibilidad de cada equipo. La tabla se calcula
    # una vez y se reusa para los motivos legibles.
    bloqueos = disponibilidad.bloqueos_por_equipo()
    for codigo in solicitud.get("equipos", []):
        # Si la propia solicitud ya lo bloqueaba, lo ignoramos: pertenece al
        # mismo flujo que estamos aprobando. Cualquier otra solicitud
        # activa sobre el mismo equipo, en cambio, si cuenta.
        bloqueos_propios = [
            s for s in bloqueos.get(codigo, []) if s.get("id") != identificador
        ]
        if bloqueos_propios:
            # El motivo tambien debe ignorar la solicitud que se esta
            # aprobando: si no, nombra a esa misma solicitud como culpable.
            motivo = disponibilidad.motivo_no_disponible(codigo, excepto=identificador) or (
                f"El equipo {codigo} no esta disponible"
            )
            raise ErrorDisponibilidad(motivo)

    modelos.registrar_cambio(solicitud, nuevo_estado, sesion.identificador)
    almacen.reemplazar("solicitudes", "id", identificador, solicitud)
    registro.evento("solicitud_aprobada", f"Solicitud {identificador} aprobada", actor=sesion.identificador)
    return solicitud


def rechazar_solicitud(sesion: Sesion, identificador: str, motivo: str) -> dict:
    """RF07.1 / RF07.2 / RF07.4: encarga pasa 'por_revisar' a 'rechazada'.

    El motivo es obligatorio (RF07.4) y se guarda tanto en el campo
    'motivo' como en el historial, para que quede registro de quien
    rechazo y por que.
    """
    if not sesion.es_encargado:
        raise ErrorPermiso(
            f"Esta operacion requiere el rol 'encargado' y la sesion es '{sesion.rol}'"
        )

    motivo_limpio = (motivo or "").strip()
    if not motivo_limpio:
        raise ErrorValidacion("El rechazo requiere un motivo no vacio")

    solicitud = almacen.obtener("solicitudes", "id", identificador)
    nuevo_estado = estados.transicionar(solicitud["estado"], "rechazar", sesion.rol)

    modelos.registrar_cambio(solicitud, nuevo_estado, sesion.identificador, motivo_limpio)
    almacen.reemplazar("solicitudes", "id", identificador, solicitud)
    registro.evento(
        "solicitud_rechazada",
        f"Solicitud {identificador} rechazada: {motivo_limpio}",
        actor=sesion.identificador,
    )
    return solicitud


def cancelar_solicitud(sesion: Sesion, identificador: str, motivo: str = "") -> dict:
    """RF09.1 / RF09.2 / RF09.3: el dueno cancela su propia solicitud.

    Solo se cancela en 'por_revisar' o 'aprobada' (RF09.2); una vez
    entregado el equipo el camino correcto es la devolucion (RF10/RF08).
    Como todavia no se entrego, los equipos vuelven a estar disponibles
    de inmediato (RF09.3) sin necesidad de tocar el estado de los
    equipos: al pasar la solicitud a 'cancelada' deja de contar como
    activa en disponibilidad.bloqueos_por_equipo().
    """
    solicitud = almacen.obtener("solicitudes", "id", identificador)
    motivo_limpio = (motivo or "").strip() or None

    if sesion.es_encargado:
        # RF09.4: el encargado tambien puede cancelar, y entonces el motivo es
        # obligatorio. Es una cancelacion que la persona no pidio, asi que
        # tiene que quedar dicho por que, y el historial lo conserva.
        if not motivo_limpio:
            raise ErrorValidacion(
                "Cuando el encargado cancela una solicitud ajena, el motivo es obligatorio"
            )
    elif solicitud.get("rut_solicitante") != sesion.identificador:
        # RF09.1: un solicitante solo cancela lo suyo.
        raise ErrorPermiso("Solo puede cancelar sus propias solicitudes")

    nuevo_estado = estados.transicionar(solicitud["estado"], "cancelar", sesion.rol)

    modelos.registrar_cambio(solicitud, nuevo_estado, sesion.identificador, motivo_limpio)
    almacen.reemplazar("solicitudes", "id", identificador, solicitud)
    registro.evento(
        "solicitud_cancelada",
        f"Solicitud {identificador} cancelada"
        + (f": {motivo_limpio}" if motivo_limpio else ""),
        actor=sesion.identificador,
    )
    return solicitud