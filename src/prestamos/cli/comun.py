"""Utilidades compartidas por los menus."""

from getpass import getpass

from ..errores import ErrorDominio
from ..registro import excepcion


def titulo(texto: str) -> None:
    print()
    print("=" * 60)
    print(texto)
    print("=" * 60)


def aviso(texto: str) -> None:
    print(f"  {texto}")


def error(texto: str) -> None:
    print(f"  [error] {texto}")


def pedir(mensaje: str, obligatorio: bool = True) -> str:
    while True:
        valor = input(f"{mensaje}: ").strip()
        if valor or not obligatorio:
            return valor
        error("El valor no puede estar vacio")


def pedir_secreto(mensaje: str) -> str:
    return getpass(f"{mensaje}: ")


def menu(opciones: list[tuple[str, str]]) -> str:
    """Muestra opciones numeradas y devuelve la clave elegida."""
    print()
    for indice, (_clave, etiqueta) in enumerate(opciones, start=1):
        print(f"  {indice}. {etiqueta}")
    print("  0. Volver / salir")
    while True:
        elegido = input("\nOpcion: ").strip()
        if elegido == "0":
            return "salir"
        if elegido.isdigit() and 1 <= int(elegido) <= len(opciones):
            return opciones[int(elegido) - 1][0]
        error("Opcion no valida")


def ejecutar(accion, actor: str = "sistema"):
    """Envuelve una operacion de servicio y traduce los errores a mensajes.

    Un ErrorDominio es una situacion prevista y se muestra al usuario. Un
    NotImplementedError marca una funcionalidad todavia no construida. Todo
    lo demas es un defecto: se registra en el log y se envia a Sentry.
    """
    try:
        return accion()
    except ErrorDominio as fallo:
        error(str(fallo))
    except NotImplementedError as pendiente:
        aviso(f"Funcionalidad pendiente ({pendiente}). Ver los Issues del repositorio.")
    except Exception as fallo:
        excepcion("error_inesperado", fallo, actor=actor)
        error("Ocurrio un error inesperado. Se registro en el log de eventos.")
    return None


def ficha(registro: dict) -> None:
    """Imprime un registro campo por campo, omitiendo los vacios.

    Un campo en None suele significar 'no aplica', por ejemplo el motivo de no
    disponibilidad de un equipo que si esta libre. Mostrarlo como 'None'
    confunde mas de lo que informa.
    """
    for clave, valor in registro.items():
        if valor in (None, "", [], {}):
            continue
        print(f"  {clave.replace('_', ' ')}: {valor}")


def tabla(filas: list[dict], columnas: list[tuple[str, str]]) -> None:
    """Imprime una tabla simple. columnas es [(clave, encabezado), ...]."""
    if not filas:
        aviso("Sin resultados")
        return
    anchos = []
    for clave, encabezado in columnas:
        ancho = max([len(encabezado)] + [len(str(fila.get(clave, ""))) for fila in filas])
        anchos.append(ancho)
    print()
    print("  " + " | ".join(e.ljust(a) for (_c, e), a in zip(columnas, anchos)))
    print("  " + "-+-".join("-" * a for a in anchos))
    for fila in filas:
        print("  " + " | ".join(str(fila.get(c, "")).ljust(a) for (c, _e), a in zip(columnas, anchos)))
    print()
