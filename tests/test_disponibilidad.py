"""Calculo de disponibilidad. Casos CP-10 a CP-13."""

import pytest

from prestamos import disponibilidad, estados

from conftest import RUT_ANA, RUT_BRUNO


@pytest.mark.funcional
def test_cp10_equipo_sin_solicitudes_esta_disponible(datos_base):
    """CP-10: sin solicitudes activas, todo el catalogo esta disponible."""
    codigos = [e["codigo"] for e in disponibilidad.equipos_disponibles()]

    assert codigos == ["LAP-001", "TAB-001", "ARD-001"]


@pytest.mark.reglas
@pytest.mark.parametrize(
    "estado",
    [estados.POR_REVISAR, estados.APROBADA, estados.EN_PRESTAMO,
     estados.PERIODO_GRACIA, estados.ATRASADA],
)
def test_cp11_todo_estado_activo_bloquea_el_equipo(datos_base, crear_solicitud_directa, estado):
    """CP-11: una solicitud por revisar bloquea igual que una en prestamo.

    Esta es la decision del equipo frente a la ambiguedad de si 'aprobada' y
    'entregada' ocupan lo mismo: ocupan igual, y ademas 'por revisar' tambien.
    """
    crear_solicitud_directa("SOL-0001", RUT_ANA, ["LAP-001"], estado)

    assert disponibilidad.esta_bloqueado("LAP-001") is True
    assert "LAP-001" not in [e["codigo"] for e in disponibilidad.equipos_disponibles()]


@pytest.mark.funcional
@pytest.mark.parametrize(
    "estado", [estados.RECHAZADA, estados.CANCELADA, estados.CONCLUIDA]
)
def test_cp12_estado_final_libera_el_equipo(datos_base, crear_solicitud_directa, estado):
    """CP-12: una solicitud cerrada deja de ocupar el equipo."""
    crear_solicitud_directa("SOL-0001", RUT_BRUNO, ["LAP-001"], estado)

    assert disponibilidad.esta_bloqueado("LAP-001") is False


@pytest.mark.negativo
def test_cp13_motivo_explica_por_que_no_se_puede_pedir(datos_base, crear_solicitud_directa):
    """CP-13: el motivo nombra la solicitud que tiene tomado el equipo."""
    crear_solicitud_directa("SOL-0001", RUT_ANA, ["LAP-001"], estados.EN_PRESTAMO)

    motivo = disponibilidad.motivo_no_disponible("LAP-001")

    assert "SOL-0001" in motivo
    assert disponibilidad.motivo_no_disponible("NO-EXISTE") == "El equipo NO-EXISTE no existe"
    assert disponibilidad.motivo_no_disponible("TAB-001") is None
