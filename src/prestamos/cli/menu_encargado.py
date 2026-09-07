"""Menu del rol encargado."""

from .. import registro
from ..servicios import equipos as srv_equipos
from ..servicios import personas as srv_personas
from ..servicios import prestamos as srv_prestamos
from ..servicios import solicitudes as srv_solicitudes
from ..sesion import Sesion
from .comun import aviso, ejecutar, ficha, menu, pedir, pedir_secreto, tabla, titulo

OPCIONES = [
    ("solicitante", "Registrar solicitante (RF02)"),
    ("encargado", "Registrar encargado (RF02)"),
    ("personas", "Ver personas autorizadas (RF02)"),
    ("estado", "Cambiar estado de un solicitante (RF02)"),
    ("equipo", "Registrar equipo (RF03)"),
    ("retirar", "Retirar o reincorporar un equipo (RF03)"),
    ("catalogo", "Ver catalogo de equipos (RF04)"),
    ("detalle", "Ver detalle de un equipo (RF04)"),
    ("solicitudes", "Ver y filtrar solicitudes (RF06)"),
    ("aprobar", "Aprobar solicitud (RF07)"),
    ("rechazar", "Rechazar solicitud (RF07)"),
    ("cancelar", "Cancelar una solicitud ajena (RF09)"),
    ("entregar", "Registrar entrega de equipos (RF08)"),
    ("confirmar", "Confirmar devolucion (RF08)"),
    ("logs", "Ver log de eventos"),
]


def mostrar(sesion: Sesion) -> None:
    while True:
        titulo(f"Encargado: {sesion.nombre} ({sesion.identificador})")
        opcion = menu(OPCIONES)
        if opcion == "salir":
            return
        _despachar(sesion, opcion)


def _despachar(sesion: Sesion, opcion: str) -> None:
    actor = sesion.identificador

    if opcion == "solicitante":
        nombre = pedir("Nombre")
        rut = pedir("RUT (12345678-9)")
        correo = pedir("Correo")
        clave = pedir_secreto("Contrasena")
        ejecutar(lambda: srv_personas.registrar_solicitante(sesion, nombre, rut, correo, clave), actor)

    elif opcion == "encargado":
        nombre = pedir("Nombre")
        correo = pedir("Correo")
        clave = pedir_secreto("Contrasena")
        ejecutar(lambda: srv_personas.registrar_encargado(sesion, nombre, correo, clave), actor)

    elif opcion == "personas":
        solicitantes = ejecutar(lambda: srv_personas.listar_solicitantes(sesion), actor)
        if solicitantes is not None:
            aviso("Solicitantes:")
            tabla(
                solicitantes,
                [("rut", "RUT"), ("nombre", "NOMBRE"), ("correo", "CORREO"), ("estado", "ESTADO")],
            )
        encargados = ejecutar(lambda: srv_personas.listar_encargados(sesion), actor)
        if encargados is not None:
            aviso("Encargados:")
            tabla(encargados, [("id", "ID"), ("nombre", "NOMBRE"), ("correo", "CORREO")])

    elif opcion == "estado":
        rut = pedir("RUT del solicitante")
        estado = pedir("Nuevo estado (al_dia / pendiente)")
        ejecutar(lambda: srv_personas.cambiar_estado_solicitante(sesion, rut, estado), actor)

    elif opcion == "equipo":
        codigo = pedir("Codigo")
        nombre = pedir("Nombre o alias")
        categoria = pedir("Categoria")
        descripcion = pedir("Descripcion", obligatorio=False)
        ejecutar(
            lambda: srv_equipos.registrar_equipo(sesion, codigo, nombre, categoria, descripcion),
            actor,
        )

    elif opcion == "retirar":
        codigo = pedir("Codigo del equipo")
        accion = pedir("Accion (retirar / reincorporar)")
        if accion.lower().startswith("rei"):
            ejecutar(lambda: srv_equipos.volver_a_servicio(sesion, codigo), actor)
        else:
            motivo = pedir("Motivo del retiro")
            ejecutar(lambda: srv_equipos.marcar_fuera_de_servicio(sesion, codigo, motivo), actor)

    elif opcion == "catalogo":
        texto = pedir("Texto a buscar (Enter para ver todos)", obligatorio=False)
        resultado = ejecutar(lambda: srv_equipos.buscar_equipos(sesion, texto), actor)
        if resultado is not None:
            tabla(
                resultado,
                [
                    ("codigo", "CODIGO"),
                    ("nombre", "NOMBRE"),
                    ("categoria", "CATEGORIA"),
                    ("estado", "ESTADO"),
                ],
            )

    elif opcion == "detalle":
        codigo = pedir("Codigo del equipo")
        resultado = ejecutar(lambda: srv_equipos.detalle_equipo(sesion, codigo), actor)
        if resultado is not None:
            ficha(resultado)

    elif opcion == "solicitudes":
        filtro = pedir("Filtro (todas / vigentes / futuras / atrasadas)", obligatorio=False)
        resultado = ejecutar(
            lambda: srv_solicitudes.listar_solicitudes(sesion, filtro or "todas"), actor
        )
        if resultado is not None:
            tabla(
                resultado,
                [
                    ("id", "ID"),
                    ("rut_solicitante", "RUT"),
                    ("equipos", "EQUIPOS"),
                    ("fecha_devolucion", "DEVOLUCION"),
                    ("estado", "ESTADO"),
                ],
            )

    elif opcion == "aprobar":
        identificador = pedir("ID de la solicitud")
        ejecutar(lambda: srv_solicitudes.aprobar_solicitud(sesion, identificador), actor)

    elif opcion == "rechazar":
        identificador = pedir("ID de la solicitud")
        motivo = pedir("Motivo del rechazo")
        ejecutar(lambda: srv_solicitudes.rechazar_solicitud(sesion, identificador, motivo), actor)

    elif opcion == "cancelar":
        identificador = pedir("ID de la solicitud")
        motivo = pedir("Motivo de la cancelacion")
        ejecutar(lambda: srv_solicitudes.cancelar_solicitud(sesion, identificador, motivo), actor)

    elif opcion == "entregar":
        identificador = pedir("ID de la solicitud")
        ejecutar(lambda: srv_prestamos.registrar_entrega(sesion, identificador), actor)

    elif opcion == "confirmar":
        identificador = pedir("ID de la solicitud")
        observacion = pedir("Observacion", obligatorio=False)
        ejecutar(lambda: srv_prestamos.confirmar_devolucion(sesion, identificador, observacion), actor)

    elif opcion == "logs":
        for linea in registro.leer_eventos(30):
            aviso(linea)
