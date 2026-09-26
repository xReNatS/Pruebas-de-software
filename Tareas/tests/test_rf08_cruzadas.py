"""RF08: entrega y confirmación de devolución. Prueba cruzada. CP-63 a CP-68.

Prueba cruzada: RF08 lo implementó el otro integrante.

Estos casos existen porque RF08 llegaba sin ninguna verificación automatizada:
los casos que lo mencionan (CP-35, CP-37 y CP-38) dependen de RF10 y de las
transiciones automáticas, que todavía no existen, así que seguían en `xfail` y
el requerimiento habría entrado a `main` sin que nada lo comprobara.
"""

from datetime import date, timedelta

import pytest

from prestamos import almacen, disponibilidad, estados, modelos, registro, reglas
from prestamos.errores import ErrorPermiso, ErrorTransicion
from prestamos.servicios import prestamos

from conftest import RUT_ANA

HOY = date.today()


@pytest.fixture
def con_solicitud(datos_base):
    """Inserta una solicitud de Ana sobre LAP-001 en el estado que se pida."""

    def _sembrar(estado, dias_devolucion=5):
        solicitud = modelos.nueva_solicitud(
            "SOL-0001", RUT_ANA, ["LAP-001"], HOY, HOY + timedelta(days=dias_devolucion)
        )
        if estado != estados.POR_REVISAR:
            modelos.registrar_cambio(solicitud, estado, "prueba")
        almacen.agregar("solicitudes", solicitud)
        return solicitud

    return _sembrar


@pytest.mark.negativo
def test_cp63_solo_el_encargado_entrega_y_confirma(con_solicitud, sesion_ana):
    """CP-63 (RF08.1): el movimiento físico lo registra quien lo presencia."""
    con_solicitud(estados.APROBADA)

    with pytest.raises(ErrorPermiso):
        prestamos.registrar_entrega(sesion_ana, "SOL-0001")
    with pytest.raises(ErrorPermiso):
        prestamos.confirmar_devolucion(sesion_ana, "SOL-0001")


@pytest.mark.funcional
def test_cp64_la_entrega_mueve_de_aprobada_a_en_prestamo(con_solicitud, sesion_encargado):
    """CP-64 (RF08.2): el camino normal de la entrega."""
    con_solicitud(estados.APROBADA)

    entregada = prestamos.registrar_entrega(sesion_encargado, "SOL-0001")

    assert entregada["estado"] == estados.EN_PRESTAMO
    assert entregada["historial"][-1]["actor"] == sesion_encargado.identificador


@pytest.mark.negativo
@pytest.mark.parametrize(
    "estado", [estados.POR_REVISAR, estados.EN_PRESTAMO, estados.CONCLUIDA, estados.CANCELADA]
)
def test_cp65_no_se_entrega_desde_otro_estado(con_solicitud, sesion_encargado, estado):
    """CP-65 (RF08.2): entregar dos veces, o antes de aprobar, no es posible."""
    con_solicitud(estado)

    with pytest.raises(ErrorTransicion):
        prestamos.registrar_entrega(sesion_encargado, "SOL-0001")


@pytest.mark.funcional
@pytest.mark.parametrize(
    "estado", [estados.EN_PRESTAMO, estados.PERIODO_GRACIA, estados.ATRASADA]
)
def test_cp66_se_concluye_desde_los_tres_estados_con_el_equipo_afuera(
    con_solicitud, sesion_encargado, estado
):
    """CP-66 (RF08.3, RF08.5): concluir cierra la solicitud y libera la unidad."""
    con_solicitud(estado)

    concluida = prestamos.confirmar_devolucion(sesion_encargado, "SOL-0001", "sin daños")

    assert concluida["estado"] == estados.CONCLUIDA
    assert disponibilidad.esta_bloqueado("LAP-001") is False


@pytest.mark.reglas
def test_cp67_devolver_tarde_no_borra_el_atraso(con_solicitud, sesion_encargado):
    """CP-67 (RF08.4, RN11): quien se atrasó queda `pendiente` aunque devuelva.

    Sin esto, atrasarse no tiene ninguna consecuencia: bastaba con devolver
    para volver a estar al día y poder pedir de inmediato, y la regla RN11
    quedaba vacía. El cambio lo hace el sistema, no el encargado que recibe
    el equipo, porque no es una decisión suya sino la regla.
    """
    con_solicitud(estados.ATRASADA)

    prestamos.confirmar_devolucion(sesion_encargado, "SOL-0001", "devuelto con retraso")

    persona = almacen.obtener("solicitantes", "rut", RUT_ANA)
    assert persona["estado"] == reglas.SOLICITANTE_PENDIENTE

    eventos = "\n".join(registro.leer_eventos(10))
    assert "estado_solicitante_cambiado" in eventos
    assert "sistema" in eventos


@pytest.mark.funcional
def test_cp68_devolver_a_tiempo_no_penaliza(con_solicitud, sesion_encargado):
    """CP-68 (RF08.4): la contracara de CP-67, para que la regla no sea un castigo ciego."""
    con_solicitud(estados.EN_PRESTAMO)

    prestamos.confirmar_devolucion(sesion_encargado, "SOL-0001", "Le falta el cargador")

    persona = almacen.obtener("solicitantes", "rut", RUT_ANA)
    assert persona["estado"] == reglas.SOLICITANTE_AL_DIA

    # RF08.6: la observación tiene que quedar en el log y en la solicitud.
    assert "cargador" in "\n".join(registro.leer_eventos(5))
    assert almacen.obtener("solicitudes", "id", "SOL-0001")["motivo"] == "Le falta el cargador"
