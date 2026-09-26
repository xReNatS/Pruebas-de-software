"""Persistencia en archivos JSON.

Un archivo por coleccion: solicitantes, encargados, equipos y solicitudes.
La escritura es atomica (archivo temporal + reemplazo) para que una caida a
mitad de guardado no deje el JSON corrupto. No hay base de datos por
requerimiento del enunciado.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from . import config
from .errores import ErrorNoEncontrado

COLECCIONES = ("solicitantes", "encargados", "equipos", "solicitudes")


def ruta(coleccion: str) -> Path:
    if coleccion not in COLECCIONES:
        raise ValueError(f"Coleccion desconocida: {coleccion}")
    return config.directorio_datos() / f"{coleccion}.json"


def leer(coleccion: str) -> list[dict[str, Any]]:
    """Devuelve la coleccion completa. Si el archivo no existe, lista vacia."""
    archivo = ruta(coleccion)
    if not archivo.exists():
        return []
    with archivo.open(encoding="utf-8") as f:
        contenido = json.load(f)
    if not isinstance(contenido, list):
        raise ValueError(f"{archivo} deberia contener una lista JSON")
    return contenido


def escribir(coleccion: str, registros: list[dict[str, Any]]) -> None:
    """Guarda la coleccion completa de forma atomica."""
    archivo = ruta(coleccion)
    archivo.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporal = tempfile.mkstemp(
        dir=str(archivo.parent), prefix=f".{coleccion}.", suffix=".tmp"
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as f:
            json.dump(registros, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(temporal, archivo)
    except BaseException:
        Path(temporal).unlink(missing_ok=True)
        raise


def buscar(coleccion: str, campo: str, valor: Any) -> dict[str, Any] | None:
    """Primer registro cuyo campo coincide, o None."""
    for registro in leer(coleccion):
        if registro.get(campo) == valor:
            return registro
    return None


def obtener(coleccion: str, campo: str, valor: Any) -> dict[str, Any]:
    """Como buscar, pero levanta ErrorNoEncontrado en vez de devolver None."""
    registro = buscar(coleccion, campo, valor)
    if registro is None:
        raise ErrorNoEncontrado(f"No existe {coleccion[:-1]} con {campo}={valor}")
    return registro


def agregar(coleccion: str, registro: dict[str, Any]) -> dict[str, Any]:
    registros = leer(coleccion)
    registros.append(registro)
    escribir(coleccion, registros)
    return registro


def reemplazar(coleccion: str, campo: str, valor: Any, nuevo: dict[str, Any]) -> dict[str, Any]:
    """Sustituye el registro identificado por campo=valor."""
    registros = leer(coleccion)
    for indice, registro in enumerate(registros):
        if registro.get(campo) == valor:
            registros[indice] = nuevo
            escribir(coleccion, registros)
            return nuevo
    raise ErrorNoEncontrado(f"No existe {coleccion[:-1]} con {campo}={valor}")


def siguiente_id(coleccion: str, prefijo: str, campo: str = "id") -> str:
    """Genera un identificador correlativo del tipo SOL-0007."""
    maximo = 0
    for registro in leer(coleccion):
        identificador = str(registro.get(campo, ""))
        if identificador.startswith(f"{prefijo}-"):
            sufijo = identificador.split("-", 1)[1]
            if sufijo.isdigit():
                maximo = max(maximo, int(sufijo))
    return f"{prefijo}-{maximo + 1:04d}"
