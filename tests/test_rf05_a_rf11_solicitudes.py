"""RF05 a RF11. Casos CP-24 en adelante.

Responsable del diseno de estas pruebas: integrante A (prueba cruzada, ya que
la implementacion de estos requerimientos corre por cuenta del integrante B).

Los casos estan marcados con xfail hasta que exista el servicio. Al implementar
el requerimiento se quita la marca y el caso debe pasar sin cambiar su cuerpo.
"""

from datetime import date, timedelta

import pytest

from prestamos import estados, reglas
from prestamos.errores import (
    ErrorDisponibilidad,
    ErrorPermiso,
    ErrorReglaNegocio,
    ErrorTransicion,
    ErrorValidacion,
)
from prestamos.servicios import prestamos as srv_prestamos
from prestamos.servicios import solicitudes as srv_solicitudes

from conftest import RUT_ANA, RUT_BRUNO

pendiente = pytest.mark.xfail(raises=NotImplementedError, reason="RF08, RF10 y RF11 no implementados")

HOY = date.today()
MANANA = HOY + timedelta(days=1)
EN_CINCO_DIAS = HOY + timedelta(days=5)


@pytest.mark.funcional
def test_cp24_crear_solicitud_valida(datos_base, sesion_ana):
    """CP-24: RF05 crea la solicitud en estado por_revisar."""
    creada = srv_solicitudes.crear_solicitud(sesion_ana, ["LAP-001"], MANANA, EN_CINCO_DIAS)

    assert creada["estado"] == estados.POR_REVISAR
    assert creada["equipos"] == ["LAP-001"]


@pytest.mark.negativo
def test_cp25_encargado_no_puede_crear_solicitudes(datos_base, sesion_encargado):
    """CP-25: solo los solicitantes generan solicitudes."""
    with pytest.raises(ErrorPermiso):
        srv_solicitudes.crear_solicitud(sesion_encargado, ["LAP-001"], MANANA, EN_CINCO_DIAS)


@pytest.mark.reglas
def test_cp26_dos_equipos_de_la_misma_categoria(datos_base, sesion_ana):
    """CP-26: dos arduinos no son combinacion valida, un arduino y una tablet si."""
    from prestamos import almacen, modelos

    almacen.agregar("equipos", modelos.nuevo_equipo("ARD-002", "Kit Arduino", "arduino"))

    with pytest.raises(ErrorReglaNegocio):
        srv_solicitudes.crear_solicitud(sesion_ana, ["ARD-001", "ARD-002"], MANANA, EN_CINCO_DIAS)

    valida = srv_solicitudes.crear_solicitud(sesion_ana, ["ARD-001", "TAB-001"], MANANA, EN_CINCO_DIAS)
    assert len(valida["equipos"]) == 2


@pytest.mark.borde
def test_cp27_tope_de_equipos_por_solicitud(datos_base, sesion_ana):
    """CP-27: cero equipos y tres equipos son invalidos."""
    with pytest.raises(ErrorValidacion):
        srv_solicitudes.crear_solicitud(sesion_ana, [], MANANA, EN_CINCO_DIAS)

    with pytest.raises(ErrorValidacion):
        srv_solicitudes.crear_solicitud(
            sesion_ana, ["LAP-001", "TAB-001", "ARD-001"], MANANA, EN_CINCO_DIAS
        )


@pytest.mark.borde
def test_cp28_duracion_maxima_de_una_semana(datos_base, sesion_ana):
    """CP-28: 7 dias exactos se acepta, 8 dias se rechaza."""
    limite = HOY + timedelta(days=reglas.DIAS_MAX_PRESTAMO)
    srv_solicitudes.crear_solicitud(sesion_ana, ["LAP-001"], HOY, limite)

    with pytest.raises(ErrorValidacion):
        srv_solicitudes.crear_solicitud(sesion_ana, ["TAB-001"], HOY, limite + timedelta(days=1))


@pytest.mark.reglas
def test_cp29_equipo_ya_tomado_por_otra_persona(datos_base, sesion_bruno, crear_solicitud_directa):
    """CP-29: gana quien pidio primero; el segundo recibe ErrorDisponibilidad."""
    crear_solicitud_directa("SOL-0001", RUT_ANA, ["LAP-001"], estados.POR_REVISAR)

    with pytest.raises(ErrorDisponibilidad):
        srv_solicitudes.crear_solicitud(sesion_bruno, ["LAP-001"], MANANA, EN_CINCO_DIAS)


@pytest.mark.reglas
def test_cp30_solicitante_pendiente_no_puede_pedir(datos_base, sesion_ana):
    """CP-30: un atraso previo bloquea nuevas solicitudes."""
    from prestamos import almacen

    persona = almacen.obtener("solicitantes", "rut", RUT_ANA)
    persona["estado"] = reglas.SOLICITANTE_PENDIENTE
    almacen.reemplazar("solicitantes", "rut", RUT_ANA, persona)

    with pytest.raises(ErrorReglaNegocio):
        srv_solicitudes.crear_solicitud(sesion_ana, ["LAP-001"], MANANA, EN_CINCO_DIAS)


@pytest.mark.reglas
def test_cp31_con_dos_equipos_en_poder_no_puede_pedir_mas(
    datos_base, sesion_ana, crear_solicitud_directa
):
    """CP-31: el tope de dos equipos simultaneos cuenta lo ya entregado."""
    crear_solicitud_directa("SOL-0001", RUT_ANA, ["LAP-001", "TAB-001"], estados.EN_PRESTAMO)

    with pytest.raises(ErrorReglaNegocio):
        srv_solicitudes.crear_solicitud(sesion_ana, ["ARD-001"], MANANA, EN_CINCO_DIAS)


@pytest.mark.funcional
def test_cp32_aprobar_y_rechazar(datos_base, sesion_encargado, crear_solicitud_directa):
    """CP-32: RF07 mueve la solicitud a aprobada o rechazada con motivo."""
    crear_solicitud_directa("SOL-0001", RUT_ANA, ["LAP-001"], estados.POR_REVISAR)
    crear_solicitud_directa("SOL-0002", RUT_BRUNO, ["TAB-001"], estados.POR_REVISAR)

    aprobada = srv_solicitudes.aprobar_solicitud(sesion_encargado, "SOL-0001")
    rechazada = srv_solicitudes.rechazar_solicitud(sesion_encargado, "SOL-0002", "Equipo en revision")

    assert aprobada["estado"] == estados.APROBADA
    assert rechazada["estado"] == estados.RECHAZADA
    assert rechazada["motivo"] == "Equipo en revision"


@pytest.mark.negativo
def test_cp33_no_se_aprueba_dos_veces(datos_base, sesion_encargado, crear_solicitud_directa):
    """CP-33: aprobar una solicitud ya aprobada levanta ErrorTransicion."""
    crear_solicitud_directa("SOL-0001", RUT_ANA, ["LAP-001"], estados.APROBADA)

    with pytest.raises(ErrorTransicion):
        srv_solicitudes.aprobar_solicitud(sesion_encargado, "SOL-0001")


@pytest.mark.negativo
def test_cp34_solicitante_no_cancela_solicitudes_ajenas(
    datos_base, sesion_bruno, crear_solicitud_directa
):
    """CP-34: RF09 solo opera sobre solicitudes propias."""
    crear_solicitud_directa("SOL-0001", RUT_ANA, ["LAP-001"], estados.POR_REVISAR)

    with pytest.raises(ErrorPermiso):
        srv_solicitudes.cancelar_solicitud(sesion_bruno, "SOL-0001")


@pendiente
@pytest.mark.reglas
def test_cp35_declarar_devolucion_no_libera_el_equipo(
    datos_base, sesion_ana, crear_solicitud_directa
):
    """CP-35: RF10 solo declara; el equipo se libera cuando RF08 confirma."""
    from prestamos import disponibilidad

    crear_solicitud_directa("SOL-0001", RUT_ANA, ["LAP-001"], estados.EN_PRESTAMO)
    srv_prestamos.declarar_devolucion(sesion_ana, "SOL-0001")

    assert disponibilidad.esta_bloqueado("LAP-001") is True


@pendiente
@pytest.mark.borde
def test_cp36_una_sola_renovacion(datos_base, sesion_ana, crear_solicitud_directa):
    """CP-36: la segunda renovacion se rechaza."""
    crear_solicitud_directa("SOL-0001", RUT_ANA, ["LAP-001"], estados.PERIODO_GRACIA)

    srv_prestamos.renovar_prestamo(sesion_ana, "SOL-0001", reglas.DIAS_MAX_RENOVACION)

    with pytest.raises(ErrorReglaNegocio):
        srv_prestamos.renovar_prestamo(sesion_ana, "SOL-0001", 3)


@pendiente
@pytest.mark.reglas
def test_cp37_atraso_deja_al_solicitante_pendiente(datos_base, crear_solicitud_directa):
    """CP-37: al pasar el periodo de gracia, la persona queda en estado pendiente."""
    from prestamos import almacen

    crear_solicitud_directa(
        "SOL-0001", RUT_ANA, ["LAP-001"], estados.PERIODO_GRACIA, dias_devolucion=-3
    )

    srv_prestamos.actualizar_estados_por_fecha(HOY)

    assert almacen.obtener("solicitudes", "id", "SOL-0001")["estado"] == estados.ATRASADA
    assert almacen.obtener("solicitantes", "rut", RUT_ANA)["estado"] == reglas.SOLICITANTE_PENDIENTE


@pendiente
@pytest.mark.escenario
def test_cp38_escenario_completo_de_solicitud_a_devolucion(datos_base, sesion_ana, sesion_encargado):
    """CP-38: recorrido completo, desde crear la solicitud hasta liberar el equipo.

    Cubre RF05, RF07, RF08 y RF10 en un solo flujo, que es el escenario de
    punta a punta exigido por la estrategia de pruebas.
    """
    from prestamos import disponibilidad

    creada = srv_solicitudes.crear_solicitud(sesion_ana, ["LAP-001"], HOY, EN_CINCO_DIAS)
    identificador = creada["id"]

    aprobada = srv_solicitudes.aprobar_solicitud(sesion_encargado, identificador)
    entregada = srv_prestamos.registrar_entrega(sesion_encargado, identificador)

    assert aprobada["estado"] == estados.APROBADA
    assert entregada["estado"] == estados.EN_PRESTAMO
    assert disponibilidad.esta_bloqueado("LAP-001") is True

    srv_prestamos.declarar_devolucion(sesion_ana, identificador)
    concluida = srv_prestamos.confirmar_devolucion(sesion_encargado, identificador, "Sin observaciones")

    assert concluida["estado"] == estados.CONCLUIDA
    assert disponibilidad.esta_bloqueado("LAP-001") is False
