"""Menu del rol solicitante."""

from datetime import date, timedelta

from ..reglas import DIAS_MAX_PRESTAMO
from ..servicios import equipos as srv_equipos
from ..servicios import prestamos as srv_prestamos
from ..servicios import solicitudes as srv_solicitudes
from ..sesion import Sesion
from .comun import aviso, ejecutar, menu, pedir, tabla, titulo

OPCIONES = [
    ("buscar", "Buscar equipos disponibles (RF04)"),
    ("detalle", "Ver detalle de un equipo (RF04)"),
    ("crear", "Crear solicitud de prestamo (RF05)"),
    ("mias", "Ver mis solicitudes (RF06)"),
    ("cancelar", "Cancelar una solicitud (RF09)"),
    ("devolver", "Declarar devolucion (RF10)"),
    ("renovar", "Renovar un prestamo (RF11)"),
]


def mostrar(sesion: Sesion) -> None:
    while True:
        titulo(f"Solicitante: {sesion.nombre} ({sesion.identificador})")
        opcion = menu(OPCIONES)
        if opcion == "salir":
            return
        _despachar(sesion, opcion)


def _despachar(sesion: Sesion, opcion: str) -> None:
    actor = sesion.identificador

    if opcion == "buscar":
        texto = pedir("Texto a buscar (Enter para ver todos)", obligatorio=False)
        resultado = ejecutar(
            lambda: srv_equipos.buscar_equipos(sesion, texto, solo_disponibles=True), actor
        )
        if resultado is not None:
            tabla(resultado, [("codigo", "CODIGO"), ("nombre", "NOMBRE"), ("categoria", "CATEGORIA")])

    elif opcion == "detalle":
        codigo = pedir("Codigo del equipo")
        resultado = ejecutar(lambda: srv_equipos.detalle_equipo(sesion, codigo), actor)
        if resultado is not None:
            for clave, valor in resultado.items():
                aviso(f"{clave}: {valor}")

    elif opcion == "crear":
        codigos = [c for c in pedir("Codigos de equipo separados por coma").split(",") if c.strip()]
        retiro = pedir(f"Fecha de retiro AAAA-MM-DD (hoy: {date.today()})")
        sugerida = date.today() + timedelta(days=DIAS_MAX_PRESTAMO)
        devolucion = pedir(f"Fecha de devolucion AAAA-MM-DD (maximo sugerido: {sugerida})")
        ejecutar(
            lambda: srv_solicitudes.crear_solicitud(
                sesion, codigos, date.fromisoformat(retiro), date.fromisoformat(devolucion)
            ),
            actor,
        )

    elif opcion == "mias":
        resultado = ejecutar(lambda: srv_solicitudes.listar_solicitudes(sesion, "mias"), actor)
        if resultado is not None:
            tabla(
                resultado,
                [
                    ("id", "ID"),
                    ("equipos", "EQUIPOS"),
                    ("fecha_retiro", "RETIRO"),
                    ("fecha_devolucion", "DEVOLUCION"),
                    ("estado", "ESTADO"),
                ],
            )

    elif opcion == "cancelar":
        identificador = pedir("ID de la solicitud")
        motivo = pedir("Motivo", obligatorio=False)
        ejecutar(lambda: srv_solicitudes.cancelar_solicitud(sesion, identificador, motivo), actor)

    elif opcion == "devolver":
        identificador = pedir("ID de la solicitud")
        ejecutar(lambda: srv_prestamos.declarar_devolucion(sesion, identificador), actor)

    elif opcion == "renovar":
        identificador = pedir("ID de la solicitud")
        dias = pedir("Dias de extension")
        ejecutar(lambda: srv_prestamos.renovar_prestamo(sesion, identificador, int(dias)), actor)
