"""Menu del rol encargado."""

from .. import registro
from ..servicios import equipos as srv_equipos
from ..servicios import personas as srv_personas
from ..servicios import prestamos as srv_prestamos
from ..servicios import solicitudes as srv_solicitudes
from ..sesion import Sesion
from .comun import aviso, ejecutar, menu, pedir, pedir_secreto, tabla, titulo

OPCIONES = [
    ("solicitante", "Registrar solicitante (RF02)"),
    ("encargado", "Registrar encargado (RF02)"),
    ("equipo", "Registrar equipo (RF03)"),
    ("catalogo", "Ver catalogo de equipos (RF04)"),
    ("solicitudes", "Ver y filtrar solicitudes (RF06)"),
    ("aprobar", "Aprobar solicitud (RF07)"),
    ("rechazar", "Rechazar solicitud (RF07)"),
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

    elif opcion == "equipo":
        codigo = pedir("Codigo")
        nombre = pedir("Nombre o alias")
        categoria = pedir("Categoria")
        descripcion = pedir("Descripcion", obligatorio=False)
        ejecutar(
            lambda: srv_equipos.registrar_equipo(sesion, codigo, nombre, categoria, descripcion),
            actor,
        )

    elif opcion == "catalogo":
        resultado = ejecutar(lambda: srv_equipos.buscar_equipos(sesion, ""), actor)
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
