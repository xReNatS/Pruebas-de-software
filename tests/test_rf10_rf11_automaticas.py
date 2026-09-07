"""RF10, RF11 y transiciones automáticas. Prueba cruzada. CP-69 a CP-77.

Prueba cruzada: estos requerimientos los implementó el otro integrante.

Los casos CP-35, CP-36 y CP-37 cubren el camino principal. Estos exploran los
criterios que aquellos no tocan, y son los que destaparon que se podía declarar
la devolución de una solicitud rechazada, que renovar tarde regalaba días, y que
los cambios automáticos no dejaban rastro en el log.
"""

from datetime import date, timedelta

import pytest

from prestamos import almacen, disponibilidad, estados, modelos, registro, reglas
from prestamos.errores import ErrorPermiso, ErrorTransicion, ErrorValidacion
from prestamos.servicios import prestamos

from conftest import RUT_ANA, RUT_BRUNO

HOY = date.today()


@pytest.fixture
def sembrar(datos_base):
    """Inserta una solicitud de Ana sobre LAP-001 en el estado y fechas pedidas."""

    def _sembrar(estado, retiro=0, devolucion=5, rut=RUT_ANA, identificador="SOL-0001"):
        solicitud = modelos.nueva_solicitud(
            identificador,
            rut,
            ["LAP-001"],
            HOY + timedelta(days=retiro),
            HOY + timedelta(days=devolucion),
        )
        if estado != estados.POR_REVISAR:
            modelos.registrar_cambio(solicitud, estado, "prueba")
        almacen.agregar("solicitudes", solicitud)
        return solicitud

    return _sembrar


# ---------------------------------------------------------------------------
# RF10 - Declarar devolución
# ---------------------------------------------------------------------------


@pytest.mark.negativo
@pytest.mark.parametrize(
    "estado",
    [estados.POR_REVISAR, estados.APROBADA, estados.CONCLUIDA,
     estados.CANCELADA, estados.RECHAZADA],
)
def test_cp69_no_se_declara_la_devolucion_de_lo_que_nunca_se_retiro(
    sembrar, sesion_ana, estado
):
    """CP-69 (RF10.5): solo se devuelve lo que se tiene en la mano.

    Sin esta comprobación se podía declarar la devolución de una solicitud
    rechazada o cancelada, es decir de equipos que nunca salieron del
    laboratorio.
    """
    sembrar(estado)

    with pytest.raises(ErrorTransicion):
        prestamos.declarar_devolucion(sesion_ana, "SOL-0001")


@pytest.mark.borde
def test_cp70_declarar_dos_veces_conserva_la_fecha_original(sembrar, sesion_ana):
    """CP-70 (RF10.4): la fecha que vale es la de la primera declaración.

    Es la que el encargado va a contrastar para decidir si hubo atraso, así
    que no puede moverse cada vez que el solicitante vuelve a apretar la
    opción del menú.
    """
    sembrar(estados.EN_PRESTAMO)
    prestamos.declarar_devolucion(sesion_ana, "SOL-0001")

    solicitud = almacen.obtener("solicitudes", "id", "SOL-0001")
    solicitud["devolucion_declarada_en"] = "2020-01-01"
    almacen.reemplazar("solicitudes", "id", "SOL-0001", solicitud)
    entradas_antes = len(solicitud["historial"])

    prestamos.declarar_devolucion(sesion_ana, "SOL-0001")

    despues = almacen.obtener("solicitudes", "id", "SOL-0001")
    assert despues["devolucion_declarada_en"] == "2020-01-01"
    assert len(despues["historial"]) == entradas_antes


@pytest.mark.negativo
def test_cp71_solo_el_dueno_declara_su_devolucion(sembrar, sesion_bruno):
    """CP-71 (RF10.1)."""
    sembrar(estados.EN_PRESTAMO)

    with pytest.raises(ErrorPermiso):
        prestamos.declarar_devolucion(sesion_bruno, "SOL-0001")


# ---------------------------------------------------------------------------
# RF11 - Renovar
# ---------------------------------------------------------------------------


@pytest.mark.reglas
def test_cp72_la_renovacion_cuenta_desde_la_devolucion_original(sembrar, sesion_ana):
    """CP-72 (RF11.5): renovar tarde no puede dar más días que renovar temprano.

    Solo se renueva en período de gracia, así que hoy siempre es posterior al
    vencimiento. Contar desde hoy regalaría días, y mientras más se demorase el
    solicitante en renovar, más ganaría.
    """
    solicitud = sembrar(estados.PERIODO_GRACIA, retiro=-8, devolucion=-1)
    original = date.fromisoformat(solicitud["fecha_devolucion"])

    prestamos.renovar_prestamo(sesion_ana, "SOL-0001", reglas.DIAS_MAX_RENOVACION)

    renovada = almacen.obtener("solicitudes", "id", "SOL-0001")
    esperada = original + timedelta(days=reglas.DIAS_MAX_RENOVACION)
    assert renovada["fecha_devolucion"] == esperada.isoformat()
    assert renovada["estado"] == estados.EN_PRESTAMO
    assert renovada["renovaciones"] == 1


@pytest.mark.negativo
@pytest.mark.parametrize("dias", [0, -3, 8])
def test_cp73_la_renovacion_rechaza_plazos_invalidos(sembrar, sesion_ana, dias):
    """CP-73 (RF11.3): cero, negativo o más del máximo.

    El caso negativo importa más de lo que parece: sin validarlo, la fecha de
    devolución se movía al pasado y la solicitud nacía vencida, el mismo
    problema que el defecto #29.
    """
    sembrar(estados.PERIODO_GRACIA, retiro=-8, devolucion=-1)

    with pytest.raises(ErrorValidacion):
        prestamos.renovar_prestamo(sesion_ana, "SOL-0001", dias)

    sin_cambios = almacen.obtener("solicitudes", "id", "SOL-0001")
    assert sin_cambios["estado"] == estados.PERIODO_GRACIA
    assert sin_cambios["renovaciones"] == 0


# ---------------------------------------------------------------------------
# Transiciones automáticas
# ---------------------------------------------------------------------------


@pytest.mark.reglas
def test_cp74_un_prestamo_muy_vencido_queda_atrasado_en_una_sola_pasada(
    sembrar, entorno_aislado
):
    """CP-74 (AUT.1, AUT.2): las transiciones se encadenan en la misma corrida.

    Si cada corrida avanzara un paso, al abrir la aplicación un préstamo
    vencido hace semanas quedaría en `periodo_gracia` y le regalaría un día de
    gracia que venció hace mucho.
    """
    sembrar(estados.EN_PRESTAMO, retiro=-30, devolucion=-20)

    prestamos.actualizar_estados_por_fecha(HOY)

    assert almacen.obtener("solicitudes", "id", "SOL-0001")["estado"] == estados.ATRASADA


@pytest.mark.funcional
def test_cp75_el_atraso_automatico_deja_pendiente_al_solicitante_y_queda_en_el_log(
    sembrar, entorno_aislado
):
    """CP-75 (AUT.3, AUT.7): el cambio automático tiene que dejar rastro.

    Nadie lo pidió y nadie lo vio ocurrir, así que si no queda en el log no
    hay forma de explicarle después al solicitante por qué está bloqueado.
    """
    sembrar(estados.PERIODO_GRACIA, retiro=-8, devolucion=-3)

    prestamos.actualizar_estados_por_fecha(HOY)

    assert almacen.obtener("solicitantes", "rut", RUT_ANA)["estado"] == reglas.SOLICITANTE_PENDIENTE

    eventos = "\n".join(registro.leer_eventos(20))
    assert "transicion_automatica" in eventos
    assert "estado_solicitante_cambiado" in eventos
    assert "sistema" in eventos


@pytest.mark.borde
def test_cp76_la_actualizacion_automatica_es_idempotente(sembrar, entorno_aislado):
    """CP-76 (AUT.6): correrla dos veces el mismo día no cambia nada la segunda."""
    sembrar(estados.EN_PRESTAMO, retiro=-8, devolucion=-3)

    primera = prestamos.actualizar_estados_por_fecha(HOY)
    segunda = prestamos.actualizar_estados_por_fecha(HOY)

    assert len(primera) == 1
    assert segunda == []


@pytest.mark.reglas
def test_cp77_una_aprobacion_sin_retiro_se_cancela_y_libera_el_equipo(
    sembrar, entorno_aislado
):
    """CP-77 (AUT.4, RN05): el plazo de retiro corre desde la aprobación.

    Sin esto, una solicitud que nadie fue a buscar inmoviliza su equipo para
    siempre, porque solo el dueño podría cancelarla.
    """
    solicitud = sembrar(estados.APROBADA, retiro=-10, devolucion=-5)
    # La aprobación quedó registrada hace diez días, no hoy.
    solicitud["historial"][-1]["en"] = (HOY - timedelta(days=10)).isoformat()
    almacen.reemplazar("solicitudes", "id", "SOL-0001", solicitud)

    prestamos.actualizar_estados_por_fecha(HOY)

    assert almacen.obtener("solicitudes", "id", "SOL-0001")["estado"] == estados.CANCELADA
    assert disponibilidad.esta_bloqueado("LAP-001") is False
