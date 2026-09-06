"""RF03 - Registrar equipo y RF04 - Consultar equipo.

Responsable: integrante A. Estado: pendiente de implementacion.

Contrato esperado y criterios de aceptacion:

RF03.1 Solo un encargado puede registrar equipos; un solicitante recibe ErrorPermiso.
RF03.2 El codigo de equipo es unico. Un codigo repetido levanta ErrorDuplicado.
RF03.3 Cada registro es una unidad fisica. Dos unidades del mismo modelo
       comparten nombre y categoria y difieren en el codigo.
RF03.4 Categoria y nombre son obligatorios; vacios levantan ErrorValidacion.

RF04.1 Un solicitante solo ve equipos disponibles; un encargado ve todos con
       su estado calculado.
RF04.2 La busqueda filtra por texto libre sobre codigo, nombre y categoria,
       sin distinguir mayusculas.
RF04.3 El detalle de un equipo no disponible indica el motivo, usando
       disponibilidad.motivo_no_disponible.
RF04.4 Consultar un codigo inexistente levanta ErrorNoEncontrado.

Puntos de apoyo ya construidos: modelos.nuevo_equipo, disponibilidad.*,
almacen.agregar, almacen.obtener.
"""

from ..sesion import Sesion


def registrar_equipo(
    sesion: Sesion, codigo: str, nombre: str, categoria: str, descripcion: str = ""
) -> dict:
    raise NotImplementedError("RF03: registrar equipo")


def marcar_fuera_de_servicio(sesion: Sesion, codigo: str, motivo: str) -> dict:
    raise NotImplementedError("RF03: marcar equipo fuera de servicio")


def buscar_equipos(sesion: Sesion, texto: str = "", solo_disponibles: bool = False) -> list[dict]:
    raise NotImplementedError("RF04: buscar equipos")


def detalle_equipo(sesion: Sesion, codigo: str) -> dict:
    raise NotImplementedError("RF04: detalle de un equipo")
