"""Log de eventos e integracion con Sentry.

Los eventos relevantes del negocio (login, aprobacion, entrega, devolucion,
atraso) se escriben en logs/eventos.log con formato estable para que el
encargado pueda revisarlos desde el menu y para que sirvan de evidencia en
el informe de pruebas.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path

from . import config

_NOMBRE_LOGGER = "prestamos"

# Directorio al que apunta el handler activo. Se guarda para poder detectar un
# cambio de directorio y reconfigurar: si el logger se configurara una sola vez
# por proceso, quedaria clavado al primer directorio y escribiria ahi aunque
# despues se apunte a otro. Eso hacia imposible verificar el log de forma
# aislada, porque cada prueba usa su propio directorio temporal.
_ruta_configurada: Path | None = None
_sentry_iniciado = False


def _configurar() -> logging.Logger:
    global _ruta_configurada

    logger = logging.getLogger(_NOMBRE_LOGGER)
    directorio = config.directorio_logs()
    if _ruta_configurada == directorio:
        return logger

    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    logger.setLevel(getattr(logging, config.nivel_log(), logging.INFO))
    logger.propagate = False

    directorio.mkdir(parents=True, exist_ok=True)

    formato = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(evento)-24s | %(actor)-24s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    archivo = logging.FileHandler(directorio / "eventos.log", encoding="utf-8")
    archivo.setFormatter(formato)
    logger.addHandler(archivo)

    _ruta_configurada = directorio
    _iniciar_sentry()
    return logger


def _iniciar_sentry() -> None:
    """Activa Sentry solo si hay DSN configurado en el .env.

    Se desactiva la creacion automatica de eventos desde el modulo logging
    (event_level=None). Por defecto, cualquier logger.error con exc_info se
    convierte en un evento de Sentry, y como esta aplicacion escribe primero
    en su log local, ese evento automatico se adelantaba al explicito: la
    deduplicacion descartaba el segundo y nos quedabamos sin identificador que
    mostrarle al usuario. Con el envio explicito el control es nuestro.

    Se conservan los registros de nivel INFO como migas de pan, para que el
    evento en Sentry llegue con el rastro de lo que hizo esa sesion.
    """
    global _sentry_iniciado

    if _sentry_iniciado or not config.sentry_dsn():
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.logging import LoggingIntegration

        sentry_sdk.init(
            dsn=config.sentry_dsn(),
            environment=config.sentry_entorno(),
            traces_sample_rate=0.0,
            send_default_pii=False,
            integrations=[LoggingIntegration(level=logging.INFO, event_level=None)],
        )
        _sentry_iniciado = True
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


def excepcion(nombre: str, error: BaseException, actor: str = "sistema") -> str | None:
    """Registra un defecto inesperado y lo reporta a Sentry si esta activo.

    Devuelve el identificador del evento en Sentry, o None si Sentry esta
    desactivado o el envio fallo. Ese identificador se le muestra a quien esta
    usando la aplicacion, para que pueda citarlo al reportar el problema y se
    pueda encontrar el evento exacto en el panel.
    """
    logger = _configurar()
    logger.error(
        f"{type(error).__name__}: {error}",
        extra={"evento": nombre, "actor": actor},
        exc_info=error,
    )

    if not config.sentry_dsn():
        return None

    try:
        import sentry_sdk

        with sentry_sdk.new_scope() as ambito:
            ambito.set_tag("evento", nombre)
            ambito.set_user({"id": actor})
            identificador = sentry_sdk.capture_exception(error)
    except Exception:  # pragma: no cover - nunca debe tumbar la aplicacion
        logger.warning(
            "No se pudo reportar el error a Sentry",
            extra={"evento": "sentry_error", "actor": actor},
        )
        return None

    if identificador:
        logger.info(
            f"Reportado a Sentry como {identificador}",
            extra={"evento": "sentry_evento", "actor": actor},
        )
    return identificador


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
