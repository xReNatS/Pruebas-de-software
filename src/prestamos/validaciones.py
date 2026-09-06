"""Validaciones de entrada reutilizables por todos los servicios."""

import re
from datetime import date

from .errores import ErrorValidacion

_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$")
_RUT = re.compile(r"^\d{7,8}-[\dkK]$")


def texto_obligatorio(valor: str | None, campo: str) -> str:
    if valor is None or not str(valor).strip():
        raise ErrorValidacion(f"El campo '{campo}' es obligatorio")
    return str(valor).strip()


def correo(valor: str | None) -> str:
    limpio = texto_obligatorio(valor, "correo").lower()
    if not _CORREO.match(limpio):
        raise ErrorValidacion(f"Correo invalido: {limpio}")
    return limpio


def contrasena(valor: str | None) -> str:
    limpio = texto_obligatorio(valor, "contrasena")
    if len(limpio) < 8:
        raise ErrorValidacion("La contrasena debe tener al menos 8 caracteres")
    return limpio


def rut(valor: str | None) -> str:
    """Normaliza a NNNNNNNN-D y verifica el digito verificador (modulo 11)."""
    limpio = texto_obligatorio(valor, "rut").replace(".", "").replace(" ", "").upper()
    if not _RUT.match(limpio):
        raise ErrorValidacion(f"RUT con formato invalido: {valor}. Se espera 12345678-9")
    cuerpo, verificador = limpio.split("-")
    if _digito_verificador(cuerpo) != verificador:
        raise ErrorValidacion(f"RUT invalido: digito verificador incorrecto en {limpio}")
    return limpio


def _digito_verificador(cuerpo: str) -> str:
    suma = 0
    multiplicador = 2
    for digito in reversed(cuerpo):
        suma += int(digito) * multiplicador
        multiplicador = 2 if multiplicador == 7 else multiplicador + 1
    resto = 11 - (suma % 11)
    if resto == 11:
        return "0"
    if resto == 10:
        return "K"
    return str(resto)


def fecha(valor: str | date | None, campo: str) -> date:
    if isinstance(valor, date):
        return valor
    limpio = texto_obligatorio(valor, campo)
    try:
        return date.fromisoformat(limpio)
    except ValueError:
        raise ErrorValidacion(f"Fecha invalida en '{campo}': {limpio}. Se espera AAAA-MM-DD")


def rango_fechas(inicio: date, fin: date) -> None:
    if fin < inicio:
        raise ErrorValidacion("La fecha de devolucion no puede ser anterior a la de retiro")


def entero_en_rango(valor: str | int | None, campo: str, minimo: int, maximo: int) -> int:
    try:
        numero = int(str(valor).strip())
    except (TypeError, ValueError):
        raise ErrorValidacion(f"El campo '{campo}' debe ser un numero entero")
    if not minimo <= numero <= maximo:
        raise ErrorValidacion(f"El campo '{campo}' debe estar entre {minimo} y {maximo}")
    return numero
