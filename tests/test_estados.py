"""Maquina de estados. Casos CP-06 a CP-09.

Se prueba la tabla de transiciones de forma aislada, sin persistencia: si
esta tabla es correcta, ningun servicio puede inventar un camino ilegal.
"""

import pytest

from prestamos import estados
from prestamos.errores import ErrorPermiso, ErrorTransicion
from prestamos.reglas import ROL_ENCARGADO, ROL_SOLICITANTE


@pytest.mark.funcional
@pytest.mark.parametrize(
    "origen,accion,rol,destino",
    [
        (estados.POR_REVISAR, "aprobar", ROL_ENCARGADO, estados.APROBADA),
        (estados.POR_REVISAR, "rechazar", ROL_ENCARGADO, estados.RECHAZADA),
        (estados.POR_REVISAR, "cancelar", ROL_SOLICITANTE, estados.CANCELADA),
        (estados.APROBADA, "entregar", ROL_ENCARGADO, estados.EN_PRESTAMO),
        (estados.EN_PRESTAMO, "vencer", estados.SISTEMA, estados.PERIODO_GRACIA),
        (estados.PERIODO_GRACIA, "renovar", ROL_SOLICITANTE, estados.EN_PRESTAMO),
        (estados.PERIODO_GRACIA, "atrasar", estados.SISTEMA, estados.ATRASADA),
        (estados.ATRASADA, "concluir", ROL_ENCARGADO, estados.CONCLUIDA),
    ],
)
def test_cp06_transiciones_validas(origen, accion, rol, destino):
    """CP-06: las transiciones del diagrama acordado se ejecutan."""
    assert estados.transicionar(origen, accion, rol) == destino


@pytest.mark.negativo
@pytest.mark.parametrize(
    "origen,accion",
    [
        (estados.CONCLUIDA, "aprobar"),
        (estados.RECHAZADA, "entregar"),
        (estados.CANCELADA, "renovar"),
        (estados.EN_PRESTAMO, "aprobar"),
        (estados.APROBADA, "renovar"),
    ],
)
def test_cp07_transiciones_inexistentes(origen, accion):
    """CP-07: una transicion fuera del diagrama levanta ErrorTransicion."""
    with pytest.raises(ErrorTransicion):
        estados.transicionar(origen, accion, ROL_ENCARGADO)


@pytest.mark.negativo
@pytest.mark.parametrize(
    "origen,accion,rol",
    [
        (estados.POR_REVISAR, "aprobar", ROL_SOLICITANTE),
        (estados.APROBADA, "entregar", ROL_SOLICITANTE),
        (estados.EN_PRESTAMO, "concluir", ROL_SOLICITANTE),
        (estados.EN_PRESTAMO, "vencer", ROL_ENCARGADO),
    ],
)
def test_cp08_transicion_con_rol_no_autorizado(origen, accion, rol):
    """CP-08: la transicion existe pero el rol no la puede ejecutar."""
    with pytest.raises(ErrorPermiso):
        estados.transicionar(origen, accion, rol)


@pytest.mark.borde
def test_cp09_estados_finales_no_tienen_salida():
    """CP-09: rechazada, concluida y cancelada no admiten ninguna accion."""
    for estado in estados.ESTADOS_FINALES:
        assert estados.acciones_posibles(estado) == []
