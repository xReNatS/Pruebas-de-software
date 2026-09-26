"""Validaciones de entrada. Casos CP-14 y CP-15."""

import pytest

from prestamos import validaciones
from prestamos.errores import ErrorValidacion


@pytest.mark.borde
@pytest.mark.parametrize(
    "entrada,esperado",
    [
        ("12345678-5", "12345678-5"),
        ("12.345.678-5", "12345678-5"),
        (" 9876543-3 ", "9876543-3"),
        ("18765436-k", "18765436-K"),
    ],
)
def test_cp14_rut_valido_se_normaliza(entrada, esperado):
    """CP-14: puntos, espacios y minusculas se normalizan al mismo formato."""
    assert validaciones.rut(entrada) == esperado


@pytest.mark.negativo
@pytest.mark.parametrize(
    "entrada",
    ["12345678-9", "123-4", "", None, "abcdefgh-1", "12345678"],
)
def test_cp15_rut_invalido_es_rechazado(entrada):
    """CP-15: formato incorrecto o digito verificador erroneo levantan error."""
    with pytest.raises(ErrorValidacion):
        validaciones.rut(entrada)
