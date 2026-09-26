"""RF06, RF07 y RF09: prueba cruzada. Casos CP-56 a CP-62.

Prueba cruzada: estos requerimientos los implementó el otro integrante. Los
casos CP-32, CP-33 y CP-34 cubren el camino principal; estos exploran los
criterios del contrato que aquellos no tocan, y son los que destaparon que el
encargado no podía cancelar ninguna solicitud.
"""

from datetime import date, timedelta

import pytest

from prestamos import almacen, disponibilidad, estados, modelos
from prestamos.errores import ErrorDisponibilidad, ErrorPermiso, ErrorValidacion
from prestamos.servicios import solicitudes

from conftest import RUT_ANA, RUT_BRUNO

HOY = date.today()


@pytest.fixture
def solicitudes_sembradas(datos_base):
    """Una solicitud por cada estado que los filtros deben distinguir."""

    def sembrar(identificador, rut, equipos, estado, dias_devolucion=5):
        solicitud = modelos.nueva_solicitud(
            identificador, rut, equipos, HOY, HOY + timedelta(days=dias_devolucion)
        )
        if estado != estados.POR_REVISAR:
            modelos.registrar_cambio(solicitud, estado, "prueba")
        almacen.agregar("solicitudes", solicitud)
        return solicitud

    sembrar("SOL-0001", RUT_ANA, ["LAP-001"], estados.POR_REVISAR)
    sembrar("SOL-0002", RUT_ANA, ["TAB-001"], estados.APROBADA)
    sembrar("SOL-0003", RUT_BRUNO, ["ARD-001"], estados.EN_PRESTAMO)
    return datos_base


# ---------------------------------------------------------------------------
# RF09 - Cancelar
# ---------------------------------------------------------------------------


@pytest.mark.funcional
def test_cp56_el_encargado_puede_cancelar_una_solicitud_ajena(
    solicitudes_sembradas, sesion_encargado
):
    """CP-56 (RF09.4): el encargado cancela, dando un motivo.

    La tabla de transiciones autoriza al encargado para la acción `cancelar`.
    Si el servicio no lo permite, esa autorización es letra muerta y el
    encargado no tiene forma de liberar un equipo comprometido por una
    solicitud que nadie va a retirar.
    """
    cancelada = solicitudes.cancelar_solicitud(
        sesion_encargado, "SOL-0001", "El equipo se reserva para clases"
    )

    assert cancelada["estado"] == estados.CANCELADA
    assert cancelada["motivo"] == "El equipo se reserva para clases"
    assert disponibilidad.esta_bloqueado("LAP-001") is False


@pytest.mark.negativo
def test_cp57_el_encargado_no_cancela_sin_motivo(solicitudes_sembradas, sesion_encargado):
    """CP-57 (RF09.4): al encargado el motivo se le exige, al dueño no.

    Es una cancelación que la persona afectada no pidió, así que tiene que
    quedar dicho por qué.
    """
    with pytest.raises(ErrorValidacion, match="motivo"):
        solicitudes.cancelar_solicitud(sesion_encargado, "SOL-0001")

    assert almacen.obtener("solicitudes", "id", "SOL-0001")["estado"] == estados.POR_REVISAR


@pytest.mark.funcional
def test_cp58_el_dueno_cancela_sin_motivo(solicitudes_sembradas, sesion_ana):
    """CP-58 (RF09.1): quien pidió el equipo puede desistir sin explicar."""
    cancelada = solicitudes.cancelar_solicitud(sesion_ana, "SOL-0001")

    assert cancelada["estado"] == estados.CANCELADA


@pytest.mark.negativo
def test_cp59_no_se_cancela_una_solicitud_ya_entregada(
    solicitudes_sembradas, sesion_encargado
):
    """CP-59 (RF09.2): con el equipo afuera, el camino es la devolución."""
    from prestamos.errores import ErrorTransicion

    with pytest.raises(ErrorTransicion):
        solicitudes.cancelar_solicitud(sesion_encargado, "SOL-0003", "me arrepentí")


# ---------------------------------------------------------------------------
# RF07 - Aprobar
# ---------------------------------------------------------------------------


@pytest.mark.reglas
def test_cp60_el_motivo_al_aprobar_no_culpa_a_la_propia_solicitud(
    solicitudes_sembradas, sesion_encargado
):
    """CP-60 (RF07.3): el mensaje debe nombrar a la solicitud que estorba.

    Toda solicitud activa bloquea sus propios equipos, así que al reaprobar
    hay que ignorarla al construir el motivo. Si no, el encargado lee que la
    solicitud está bloqueada por sí misma, que es cierto e inútil.
    """
    otra = modelos.nueva_solicitud(
        "SOL-0099", RUT_BRUNO, ["LAP-001"], HOY, HOY + timedelta(days=3)
    )
    modelos.registrar_cambio(otra, estados.EN_PRESTAMO, "prueba")
    almacen.agregar("solicitudes", otra)

    with pytest.raises(ErrorDisponibilidad) as fallo:
        solicitudes.aprobar_solicitud(sesion_encargado, "SOL-0001")

    assert "SOL-0099" in str(fallo.value)
    assert "SOL-0001" not in str(fallo.value)


@pytest.mark.funcional
def test_cp61_se_aprueba_aunque_la_propia_solicitud_bloquee_su_equipo(
    solicitudes_sembradas, sesion_encargado
):
    """CP-61 (RF07.3): la revalidación no puede bloquearse a sí misma."""
    aprobada = solicitudes.aprobar_solicitud(sesion_encargado, "SOL-0001")

    assert aprobada["estado"] == estados.APROBADA


# ---------------------------------------------------------------------------
# RF06 - Consultar
# ---------------------------------------------------------------------------


@pytest.mark.negativo
def test_cp62_un_solicitante_no_ve_lo_ajeno_pida_el_filtro_que_pida(
    solicitudes_sembradas, sesion_ana
):
    """CP-62 (RF06.1): cambiar el nombre del filtro no es una vía de escape.

    Se comprueba con todos los filtros y no solo con el que usa el menú,
    porque la restricción tiene que vivir en el servicio y no en la interfaz.
    """
    for filtro in ("todas", "mias", "vigentes", "futuras", "atrasadas"):
        visibles = solicitudes.listar_solicitudes(sesion_ana, filtro)
        ajenas = [s["id"] for s in visibles if s["rut_solicitante"] != RUT_ANA]
        assert not ajenas, f"con el filtro {filtro} se filtraron solicitudes ajenas: {ajenas}"

    with pytest.raises(ErrorValidacion):
        solicitudes.listar_solicitudes(sesion_ana, "inventado")

    with pytest.raises(ErrorPermiso):
        solicitudes.detalle_solicitud(sesion_ana, "SOL-0003")
