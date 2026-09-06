"""Configuracion central: rutas de datos y variables de entorno."""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - la app funciona sin python-dotenv
    def load_dotenv(*_args, **_kwargs):
        return False

RAIZ_PROYECTO = Path(__file__).resolve().parents[2]

load_dotenv(RAIZ_PROYECTO / ".env")


def directorio_datos() -> Path:
    """Directorio de los archivos JSON.

    Se lee de PRESTAMOS_DIR_DATOS para que las pruebas puedan apuntar a un
    directorio temporal sin tocar los datos de demostracion.
    """
    ruta = os.environ.get("PRESTAMOS_DIR_DATOS")
    return Path(ruta) if ruta else RAIZ_PROYECTO / "data"


def directorio_logs() -> Path:
    ruta = os.environ.get("PRESTAMOS_DIR_LOGS")
    return Path(ruta) if ruta else RAIZ_PROYECTO / "logs"


SENTRY_DSN = os.environ.get("SENTRY_DSN", "").strip()
SENTRY_ENTORNO = os.environ.get("SENTRY_ENTORNO", "desarrollo")
NIVEL_LOG = os.environ.get("NIVEL_LOG", "INFO").upper()
