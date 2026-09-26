"""RF01 - Inicio de sesion. Casos CP-01 a CP-04.

Estas pruebas son la referencia de estilo para el resto del equipo: cada
funcion documenta el caso de prueba, su categoria y el criterio que verifica.
"""

import pytest

from prestamos.errores import ErrorAutenticacion
from prestamos.reglas import ROL_ENCARGADO, ROL_SOLICITANTE
from prestamos.servicios import autenticacion

from conftest import CLAVE_ENCARGADO, CLAVE_SOLICITANTE, RUT_ANA


@pytest.mark.funcional
def test_cp01_login_encargado_correcto(datos_base):
    """CP-01: credenciales validas de encargado devuelven una sesion con rol encargado."""
    sesion = autenticacion.iniciar_sesion("camila@lab.cl", CLAVE_ENCARGADO)

    assert sesion.rol == ROL_ENCARGADO
    assert sesion.identificador == "ENC-0001"
    assert sesion.es_encargado is True


@pytest.mark.funcional
def test_cp02_login_solicitante_correcto(datos_base):
    """CP-02: el solicitante entra con su correo y queda identificado por su RUT."""
    sesion = autenticacion.iniciar_sesion("ana@alumnos.cl", CLAVE_SOLICITANTE)

    assert sesion.rol == ROL_SOLICITANTE
    assert sesion.identificador == RUT_ANA


@pytest.mark.negativo
@pytest.mark.parametrize(
    "correo,clave",
    [
        ("ana@alumnos.cl", "clave-incorrecta"),
        ("noexiste@alumnos.cl", CLAVE_SOLICITANTE),
        ("ana@alumnos.cl", ""),
        ("sin-arroba", CLAVE_SOLICITANTE),
    ],
)
def test_cp03_credenciales_invalidas(datos_base, correo, clave):
    """CP-03: toda credencial invalida falla con el mismo mensaje generico.

    El mensaje no debe revelar si el correo existe, para no facilitar la
    enumeracion de cuentas.
    """
    with pytest.raises(ErrorAutenticacion) as fallo:
        autenticacion.iniciar_sesion(correo, clave)

    assert str(fallo.value) == "Correo o contrasena incorrectos"


@pytest.mark.borde
def test_cp04_correo_no_distingue_mayusculas_ni_espacios(datos_base):
    """CP-04: el correo se normaliza antes de buscar la cuenta."""
    sesion = autenticacion.iniciar_sesion("  ANA@Alumnos.CL  ", CLAVE_SOLICITANTE)

    assert sesion.identificador == RUT_ANA


@pytest.mark.negativo
def test_cp05_contrasena_no_se_guarda_en_texto_plano(datos_base):
    """CP-05: el JSON de solicitantes no contiene la contrasena legible."""
    from prestamos import almacen

    registro = almacen.obtener("solicitantes", "rut", RUT_ANA)

    assert "contrasena" not in registro
    assert CLAVE_SOLICITANTE not in registro["contrasena_hash"]
    assert registro["contrasena_hash"].startswith("pbkdf2_sha256$")
