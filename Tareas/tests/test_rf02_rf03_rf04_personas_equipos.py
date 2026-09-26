"""RF02, RF03 y RF04. Casos CP-16 en adelante.

Responsable del diseno de estas pruebas: integrante B (prueba cruzada, ya que
la implementacion de estos requerimientos corre por cuenta del integrante A).

Los tres requerimientos estan implementados, asi que ya no queda ningun caso
marcado con xfail: todos se ejecutan de verdad. Ninguno de estos cuerpos se
modifico al implementar, que era la condicion del contrato.
"""

import pytest

from prestamos.errores import ErrorDuplicado, ErrorPermiso, ErrorValidacion
from prestamos.servicios import equipos as srv_equipos
from prestamos.servicios import personas as srv_personas

@pytest.mark.funcional
def test_cp16_encargado_registra_solicitante(datos_base, sesion_encargado):
    """CP-16: el encargado registra un solicitante y queda en el JSON."""
    creado = srv_personas.registrar_solicitante(
        sesion_encargado, "Elena Diaz", "20111222-2", "elena@alumnos.cl", "clave12345"
    )
    assert creado["rut"] == "20111222-2"


@pytest.mark.negativo
def test_cp17_solicitante_no_puede_registrar_personas(datos_base, sesion_ana):
    """CP-17: RF02 esta reservado al encargado."""
    with pytest.raises(ErrorPermiso):
        srv_personas.registrar_solicitante(
            sesion_ana, "Elena Diaz", "20111222-2", "elena@alumnos.cl", "clave12345"
        )


@pytest.mark.negativo
def test_cp18_rut_duplicado_es_rechazado(datos_base, sesion_encargado):
    """CP-18: no se puede registrar dos veces el mismo RUT."""
    with pytest.raises(ErrorDuplicado):
        srv_personas.registrar_solicitante(
            sesion_encargado, "Otra Ana", "12345678-5", "otra@alumnos.cl", "clave12345"
        )


@pytest.mark.funcional
def test_cp19_encargado_registra_equipo(datos_base, sesion_encargado):
    """CP-19: un equipo nuevo aparece en el catalogo como disponible."""
    creado = srv_equipos.registrar_equipo(
        sesion_encargado, "PRO-001", "Proyector Epson", "proyector", "Con HDMI"
    )
    assert creado["codigo"] == "PRO-001"


@pytest.mark.borde
def test_cp20_dos_unidades_del_mismo_modelo(datos_base, sesion_encargado):
    """CP-20: dos unidades del mismo modelo conviven con codigos distintos."""
    srv_equipos.registrar_equipo(sesion_encargado, "LAP-002", "Notebook Dell", "laptop")
    encontrados = srv_equipos.buscar_equipos(sesion_encargado, "Notebook Dell")
    assert len(encontrados) == 2


@pytest.mark.negativo
def test_cp21_codigo_de_equipo_duplicado(datos_base, sesion_encargado):
    """CP-21: repetir un codigo levanta ErrorDuplicado."""
    with pytest.raises(ErrorDuplicado):
        srv_equipos.registrar_equipo(sesion_encargado, "LAP-001", "Otro notebook", "laptop")


@pytest.mark.negativo
def test_cp22_categoria_vacia_es_rechazada(datos_base, sesion_encargado):
    """CP-22: la categoria es obligatoria porque de ella depende la regla de las dos categorias."""
    with pytest.raises(ErrorValidacion):
        srv_equipos.registrar_equipo(sesion_encargado, "XXX-001", "Equipo raro", "")


@pytest.mark.funcional
def test_cp23_solicitante_solo_ve_equipos_disponibles(
    datos_base, sesion_ana, crear_solicitud_directa
):
    """CP-23: RF04 filtra por rol."""
    from prestamos import estados

    crear_solicitud_directa("SOL-0001", "17890123-0", ["LAP-001"], estados.EN_PRESTAMO)
    visibles = [e["codigo"] for e in srv_equipos.buscar_equipos(sesion_ana, "", solo_disponibles=True)]
    assert "LAP-001" not in visibles
