"""Fabricas de entidades.

Las entidades se representan como diccionarios porque se guardan tal cual en
JSON. Cada fabrica valida sus campos y fija el esquema, de modo que el
esquema del archivo esta definido en un solo lugar del codigo.
"""

from datetime import date

from . import reglas, seguridad, validaciones
from .disponibilidad import EQUIPO_DISPONIBLE
from .estados import POR_REVISAR
from .registro import ahora_iso


def nuevo_solicitante(nombre: str, rut: str, correo: str, contrasena: str) -> dict:
    """Solicitante: nombre, RUT, correo, contrasena y estado (al dia / pendiente)."""
    return {
        "rut": validaciones.rut(rut),
        "nombre": validaciones.texto_obligatorio(nombre, "nombre"),
        "correo": validaciones.correo(correo),
        "contrasena_hash": seguridad.hashear(validaciones.contrasena(contrasena)),
        "estado": reglas.SOLICITANTE_AL_DIA,
        "creado_en": ahora_iso(),
    }


def nuevo_encargado(identificador: str, nombre: str, correo: str, contrasena: str) -> dict:
    """Encargado: id, nombre, correo y contrasena."""
    return {
        "id": validaciones.texto_obligatorio(identificador, "id"),
        "nombre": validaciones.texto_obligatorio(nombre, "nombre"),
        "correo": validaciones.correo(correo),
        "contrasena_hash": seguridad.hashear(validaciones.contrasena(contrasena)),
        "creado_en": ahora_iso(),
    }


def nuevo_equipo(codigo: str, nombre: str, categoria: str, descripcion: str = "") -> dict:
    """Equipo: cada registro es una unidad fisica, no un modelo.

    Varias unidades del mismo modelo comparten nombre y categoria pero tienen
    codigos distintos, que es lo que permite calcular disponibilidad por unidad.
    """
    return {
        "codigo": validaciones.texto_obligatorio(codigo, "codigo").upper(),
        "nombre": validaciones.texto_obligatorio(nombre, "nombre"),
        "categoria": validaciones.texto_obligatorio(categoria, "categoria").lower(),
        "estado": EQUIPO_DISPONIBLE,
        "descripcion": (descripcion or "").strip(),
        "creado_en": ahora_iso(),
    }


def nueva_solicitud(
    identificador: str,
    rut_solicitante: str,
    codigos_equipos: list[str],
    fecha_retiro: date,
    fecha_devolucion: date,
) -> dict:
    """Solicitud: solicitante, equipos, fechas y estado.

    Nace siempre en 'por_revisar'. Los campos de auditoria (historial,
    renovaciones, devolucion declarada) viven en la misma entidad para que el
    informe de trazabilidad se pueda armar leyendo un solo archivo.
    """
    return {
        "id": validaciones.texto_obligatorio(identificador, "id"),
        "rut_solicitante": validaciones.rut(rut_solicitante),
        "equipos": [c.strip().upper() for c in codigos_equipos],
        "fecha_retiro": fecha_retiro.isoformat(),
        "fecha_devolucion": fecha_devolucion.isoformat(),
        "estado": POR_REVISAR,
        "renovaciones": 0,
        "devolucion_declarada_en": None,
        "motivo": None,
        "creado_en": ahora_iso(),
        "historial": [{"estado": POR_REVISAR, "en": ahora_iso(), "actor": rut_solicitante}],
    }


def registrar_cambio(solicitud: dict, estado: str, actor: str, motivo: str | None = None) -> dict:
    """Anota una transicion en el historial de la solicitud."""
    solicitud["estado"] = estado
    if motivo:
        solicitud["motivo"] = motivo
    solicitud.setdefault("historial", []).append(
        {"estado": estado, "en": ahora_iso(), "actor": actor, "motivo": motivo}
    )
    return solicitud
