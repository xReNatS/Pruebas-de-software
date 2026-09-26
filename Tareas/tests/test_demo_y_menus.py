"""Datos de demostración y guion. Casos CP-44 a CP-48.

Cubren el Issue #13. No son prueba cruzada: verifican que la demostración sea
reproducible, no un requerimiento funcional repartido entre los integrantes.

El valor de estos casos es que el guion de `docs/guion-demostracion.md` deja de
depender de que alguien lo verifique a ojo antes de la entrega.
"""

import pytest

from prestamos import almacen, demo, disponibilidad, estados, reglas
from prestamos.cli import menu_encargado, menu_solicitante

# Orden de las opciones tal como las cita el guion de demostración. Si alguien
# reordena un menú, este caso falla y recuerda actualizar el documento antes de
# que un profesor siga pasos que ya no corresponden.
OPCIONES_ENCARGADO = [
    "solicitante", "encargado", "personas", "estado",
    "equipo", "retirar", "catalogo", "detalle",
    "solicitudes", "aprobar", "rechazar", "cancelar", "entregar", "confirmar", "logs",
]

OPCIONES_SOLICITANTE = [
    "buscar", "detalle", "crear", "mias", "cancelar", "devolver", "renovar",
]


@pytest.fixture
def demo_cargada(entorno_aislado):
    """Carga el escenario de demostración en el directorio temporal."""
    demo.cargar(forzar=True)
    return entorno_aislado


@pytest.mark.borde
def test_cp44_el_orden_de_los_menus_coincide_con_el_guion():
    """CP-44: el guion cita números de opción; este caso los ancla."""
    assert [clave for clave, _ in menu_encargado.OPCIONES] == OPCIONES_ENCARGADO
    assert [clave for clave, _ in menu_solicitante.OPCIONES] == OPCIONES_SOLICITANTE


@pytest.mark.funcional
def test_cp45_la_demo_tiene_un_ejemplo_de_cada_estado(demo_cargada):
    """CP-45 (DEM.1): se puede mostrar cualquier estado sin esperar días."""
    presentes = {s["estado"] for s in almacen.leer("solicitudes")}

    assert presentes == set(estados.ESTADOS)


@pytest.mark.funcional
def test_cp46_la_demo_tiene_un_solicitante_pendiente(demo_cargada):
    """CP-46 (DEM.2): hace falta para mostrar el bloqueo por atraso."""
    personas = almacen.leer("solicitantes")
    pendientes = [p for p in personas if p["estado"] == reglas.SOLICITANTE_PENDIENTE]

    assert len(pendientes) >= 1
    # Su atraso debe ser real, no un estado escrito a mano sin respaldo.
    atrasadas = [
        s for s in almacen.leer("solicitudes")
        if s["estado"] == estados.ATRASADA and s["rut_solicitante"] == pendientes[0]["rut"]
    ]
    assert atrasadas, "el solicitante pendiente no tiene ninguna solicitud atrasada que lo explique"


@pytest.mark.reglas
def test_cp47_la_demo_muestra_los_tres_estados_de_un_equipo(demo_cargada):
    """CP-47: disponible, en uso y fuera de servicio, los tres visibles."""
    bloqueos = disponibilidad.bloqueos_por_equipo()
    calculados = {
        disponibilidad.estado_calculado(e, bloqueos) for e in almacen.leer("equipos")
    }

    assert calculados == {
        disponibilidad.EQUIPO_DISPONIBLE,
        disponibilidad.EQUIPO_EN_USO,
        disponibilidad.EQUIPO_FUERA_SERVICIO,
    }


@pytest.mark.borde
def test_cp48_la_demo_es_reproducible(demo_cargada):
    """CP-48 (DEM.4): volver a cargarla deja el mismo escenario, no lo duplica."""
    antes = {c: len(almacen.leer(c)) for c in almacen.COLECCIONES}

    demo.cargar(forzar=True)

    assert {c: len(almacen.leer(c)) for c in almacen.COLECCIONES} == antes


@pytest.mark.negativo
def test_cp49_la_demo_no_pisa_datos_existentes_sin_forzar(demo_cargada):
    """CP-49: sin --forzar el script se niega, para no borrar lo que hay."""
    with pytest.raises(SystemExit):
        demo.cargar(forzar=False)
