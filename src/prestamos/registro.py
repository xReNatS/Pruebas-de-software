"""Log de eventos e integracion con Sentry.

Los eventos relevantes del negocio (login, aprobacion, entrega, devolucion,
atraso) se escriben en logs/eventos.log con formato estable para que el
encargado pueda revisarlos desde el menu y para que sirvan de evidencia en
el informe de pruebas.
"""

import logging
from datetime import datetime, timezone

from . import config

_NOMBRE_LOGGER = "prestamos"
_configurado = False


def _configurar() -> logging.Logger:
    global _configurado
    logger = logging.getLogger(_NOMBRE_LOGGER)
    if _configurado:
        return logger

    logger.setLevel(getattr(logging, config.NIVEL_LOG, logging.INFO))
    logger.propagate = False

    directorio = config.directorio_logs()
    directorio.mkdir(parents=True, exist_ok=True)

    formato = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(evento)-24s | %(actor)-24s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    archivo = logging.FileHandler(directorio / "eventos.log", encoding="utf-8")
    archivo.setFormatter(formato)
    logger.addHandler(archivo)

    _configurado = True
    _iniciar_sentry()
    return logger


def _iniciar_sentry() -> None:
    """Activa Sentry solo si hay DSN configurado en el .env."""
    if not config.SENTRY_DSN:
        return
    try:
        import sentry_sdk

        sentry_sdk.init(
            dsn=config.SENTRY_DSN,
            environment=config.SENTRY_ENTORNO,
            traces_sample_rate=0.0,
            send_default_pii=False,
        )
    except Exception:  # pragma: no cover - nunca debe tumbar la aplicacion
        logging.getLogger(_NOMBRE_LOGGER).warning(
            "No se pudo iniciar Sentry",
            extra={"evento": "sentry_error", "actor": "sistema"},
        )


def evento(nombre: str, mensaje: str, actor: str = "sistema", nivel: str = "INFO") -> None:
    """Registra un evento de negocio."""
    logger = _configurar()
    logger.log(
        getattr(logging, nivel, logging.INFO),
        mensaje,
        extra={"evento": nombre, "actor": actor},
    )


def excepcion(nombre: str, error: BaseException, actor: str = "sistema") -> None:
    """Registra un defecto inesperado y lo reporta a Sentry si esta activo."""
    logger = _configurar()
    logger.error(
        f"{type(error).__name__}: {error}",
        extra={"evento": nombre, "actor": actor},
        exc_info=error,
    )
    if config.SENTRY_DSN:
        try:
            import sentry_sdk

            sentry_sdk.capture_exception(error)
        except Exception:  # pragma: no cover
            pass


def leer_eventos(maximo: int = 50) -> list[str]:
    """Ultimas lineas del log, para la vista de logs del encargado (RF12)."""
    ruta = config.directorio_logs() / "eventos.log"
    if not ruta.exists():
        return []
    with ruta.open(encoding="utf-8") as archivo:
        lineas = archivo.readlines()
    return [linea.rstrip("\n") for linea in lineas[-maximo:]]


def ahora_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
