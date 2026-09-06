"""Fixtures compartidas por toda la suite.

Regla del equipo: ninguna prueba toca data/. Cada prueba recibe un directorio
temporal propio, de modo que se pueden ejecutar en cualquier orden y no
ensucian los datos de demostracion.
"""

import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from prestamos import almacen, estados, modelos  # noqa: E402
from prestamos.reglas import ROL_ENCARGADO, ROL_SOLICITANTE  # noqa: E402
from prestamos.sesion import Sesion  # noqa: E402

CLAVE_ENCARGADO = "labadmin2026"
CLAVE_SOLICITANTE = "demo12345"

RUT_ANA = "12345678-5"
RUT_BRUNO = "17890123-0"


@pytest.fixture(autouse=True)
def entorno_aislado(tmp_path, monkeypatch):
    """Redirige datos y logs a un directorio temporal."""
    monkeypatch.setenv("PRESTAMOS_DIR_DATOS", str(tmp_path / "data"))
    monkeypatch.setenv("PRESTAMOS_DIR_LOGS", str(tmp_path / "logs"))
    monkeypatch.setenv("SENTRY_DSN", "")
    (tmp_path / "data").mkdir()
    return tmp_path


@pytest.fixture
def datos_base(entorno_aislado):
    """Dos personas, tres equipos y ninguna solicitud."""
    almacen.escribir(
        "encargados",
        [modelos.nuevo_encargado("ENC-0001", "Camila Rojas", "camila@lab.cl", CLAVE_ENCARGADO)],
    )
    almacen.escribir(
        "solicitantes",
        [
            modelos.nuevo_solicitante("Ana Perez", RUT_ANA, "ana@alumnos.cl", CLAVE_SOLICITANTE),
            modelos.nuevo_solicitante("Bruno Silva", RUT_BRUNO, "bruno@alumnos.cl", CLAVE_SOLICITANTE),
        ],
    )
    almacen.escribir(
        "equipos",
        [
            modelos.nuevo_equipo("LAP-001", "Notebook Dell", "laptop", "16 GB RAM"),
            modelos.nuevo_equipo("TAB-001", "Tablet Samsung", "tablet", "Con lapiz"),
            modelos.nuevo_equipo("ARD-001", "Kit Arduino", "arduino", "Kit completo"),
        ],
    )
    almacen.escribir("solicitudes", [])
    return entorno_aislado


@pytest.fixture
def sesion_encargado():
    return Sesion(ROL_ENCARGADO, "ENC-0001", "Camila Rojas", "camila@lab.cl")


@pytest.fixture
def sesion_ana():
    return Sesion(ROL_SOLICITANTE, RUT_ANA, "Ana Perez", "ana@alumnos.cl")


@pytest.fixture
def sesion_bruno():
    return Sesion(ROL_SOLICITANTE, RUT_BRUNO, "Bruno Silva", "bruno@alumnos.cl")


@pytest.fixture
def crear_solicitud_directa():
    """Inserta una solicitud en un estado dado sin pasar por los servicios.

    Sirve para montar escenarios de borde (atrasos, periodo de gracia) sin
    tener que esperar dias reales ni depender de codigo aun no implementado.
    """

    def _crear(identificador, rut, equipos, estado, dias_retiro=0, dias_devolucion=5):
        hoy = date.today()
        solicitud = modelos.nueva_solicitud(
            identificador,
            rut,
            equipos,
            hoy + timedelta(days=dias_retiro),
            hoy + timedelta(days=dias_devolucion),
        )
        if estado != estados.POR_REVISAR:
            modelos.registrar_cambio(solicitud, estado, "prueba")
        almacen.agregar("solicitudes", solicitud)
        return solicitud

    return _crear
