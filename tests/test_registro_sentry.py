"""Log de eventos e integracion con Sentry. Casos CP-39 a CP-43.

Estos casos no son parte de la prueba cruzada: cubren infraestructura propia
del Issue #12, no un requerimiento funcional repartido entre los integrantes.

No se comprueba que el evento llegue al panel de Sentry, porque eso exigiria
red y un DSN real. Lo que si se comprueba es todo lo que esta bajo nuestro
control: que Sentry quede apagado en las pruebas, que un error previsto no se
reporte nunca, y que un defecto inesperado quede registrado sin tumbar la
aplicacion. La verificacion contra el panel real esta documentada aparte.
"""

import pytest

from prestamos import config, registro
from prestamos.cli import comun
from prestamos.errores import ErrorValidacion


@pytest.mark.negativo
def test_cp39_sentry_apagado_durante_las_pruebas(datos_base):
    """CP-39: la suite no puede enviar eventos reales al panel del proyecto.

    Es la razon por la que el DSN se lee con una funcion y no con una
    constante de modulo: si se leyera al importar, el monkeypatch de la
    fixture llegaria tarde y cada ejecucion de la suite ensuciaria Sentry.
    """
    registro.evento("prueba", "fuerza la configuracion del logger", actor="prueba")

    import sentry_sdk

    assert config.sentry_dsn() == ""
    assert not sentry_sdk.get_client().is_active()


@pytest.mark.funcional
def test_cp40_los_eventos_quedan_en_el_log_con_su_actor(datos_base):
    """CP-40: cada evento registra que paso, quien lo hizo y cuando."""
    registro.evento("equipo_registrado", "Alta de equipo LAP-009", actor="ENC-0001")

    ultima = registro.leer_eventos(1)[0]

    assert "equipo_registrado" in ultima
    assert "ENC-0001" in ultima
    assert "Alta de equipo LAP-009" in ultima


@pytest.mark.negativo
def test_cp41_un_defecto_queda_registrado_sin_dsn(datos_base):
    """CP-41: sin Sentry, el defecto igual se registra y no hay identificador."""
    identificador = registro.excepcion(
        "error_inesperado", ValueError("archivo corrupto"), actor="ENC-0001"
    )

    ultimas = "\n".join(registro.leer_eventos(10))

    assert identificador is None
    assert "error_inesperado" in ultimas
    assert "ValueError: archivo corrupto" in ultimas


@pytest.mark.negativo
def test_cp42_un_error_previsto_no_se_reporta_como_defecto(datos_base, capsys):
    """CP-42: un ErrorDominio se muestra al usuario y no genera reporte.

    Si los errores de negocio se reportaran, el panel se llenaria de RUT mal
    escritos y dejaria de servir para encontrar defectos reales.
    """
    def accion():
        raise ErrorValidacion("RUT invalido: digito verificador incorrecto")

    resultado = comun.ejecutar(accion, actor="ENC-0001")
    mostrado = capsys.readouterr().out

    assert resultado is None
    assert "RUT invalido" in mostrado
    assert "error inesperado" not in mostrado.lower()
    assert "error_inesperado" not in "\n".join(registro.leer_eventos(10))


@pytest.mark.borde
def test_cp43_un_defecto_inesperado_no_tumba_la_interfaz(datos_base, capsys):
    """CP-43: la interfaz atrapa lo imprevisto y lo convierte en mensaje."""
    def accion():
        raise ZeroDivisionError("division by zero")

    resultado = comun.ejecutar(accion, actor="ENC-0001")
    mostrado = capsys.readouterr().out

    assert resultado is None
    assert "Ocurrio un error inesperado" in mostrado
    assert "ZeroDivisionError" in "\n".join(registro.leer_eventos(10))
