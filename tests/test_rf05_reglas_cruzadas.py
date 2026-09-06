"""RF05, casos que combinan reglas o intentan romperlas. CP-50 a CP-55.

Prueba cruzada: RF05 lo implementó el otro integrante. Estos casos exploran
lo que los casos CP-24 a CP-31 no cubren, que es lo que pasa cuando las
reglas se combinan entre varias solicitudes en vez de dentro de una sola.

Los casos marcados `xfail(strict=True)` documentan defectos abiertos. Cuando
se corrijan, el caso pasará y `strict` hará fallar la suite, lo que obliga a
quitar la marca en vez de dejarla puesta para siempre.
"""

from datetime import date, timedelta

import pytest

from prestamos import almacen, estados, modelos, reglas
from prestamos.errores import ErrorDisponibilidad, ErrorDominio, ErrorValidacion
from prestamos.servicios import solicitudes

from conftest import RUT_ANA

HOY = date.today()
EN_TRES_DIAS = HOY + timedelta(days=3)


@pytest.fixture
def catalogo_amplio(datos_base):
    """Seis unidades, tres de ellas laptops, para poder combinar categorías."""
    for codigo, nombre, categoria in [
        ("LAP-002", "Notebook B", "laptop"),
        ("LAP-003", "Notebook C", "laptop"),
        ("CAM-001", "Camara A", "camara"),
    ]:
        almacen.agregar("equipos", modelos.nuevo_equipo(codigo, nombre, categoria))
    return datos_base


def equipos_en_poder_de(rut: str) -> list[str]:
    """Códigos que la persona tendría si se aprobaran todas sus solicitudes vivas."""
    return [
        codigo
        for solicitud in almacen.leer("solicitudes")
        if solicitud["rut_solicitante"] == rut and solicitud["estado"] in estados.ESTADOS_ACTIVOS
        for codigo in solicitud["equipos"]
    ]


@pytest.mark.reglas
def test_cp50_varias_solicitudes_no_pueden_superar_el_tope(catalogo_amplio, sesion_ana):
    """CP-50: RN01 limita a 2 equipos simultáneos, no a 2 por solicitud.

    Si cada solicitud se valida sola, basta con partir el pedido en varias para
    saltarse el límite. Ninguna cuenta hasta que el encargado la entrega, y para
    entonces ya están todas aprobadas.
    """
    solicitudes.crear_solicitud(sesion_ana, ["LAP-001", "TAB-001"], HOY, EN_TRES_DIAS)

    with pytest.raises(ErrorDominio):
        solicitudes.crear_solicitud(sesion_ana, ["ARD-001", "CAM-001"], HOY, EN_TRES_DIAS)

    assert len(equipos_en_poder_de(RUT_ANA)) <= reglas.MAX_EQUIPOS_SIMULTANEOS


@pytest.mark.reglas
def test_cp51_dos_solicitudes_no_pueden_dar_dos_equipos_de_la_misma_categoria(
    catalogo_amplio, sesion_ana
):
    """CP-51: RN02 habla de los equipos en poder de una persona, no de una solicitud.

    Pedir dos laptops en la misma solicitud se rechaza. Pedirlas en dos
    solicitudes seguidas, no. El resultado físico es idéntico.
    """
    solicitudes.crear_solicitud(sesion_ana, ["LAP-001"], HOY, EN_TRES_DIAS)

    with pytest.raises(ErrorDominio):
        solicitudes.crear_solicitud(sesion_ana, ["LAP-002"], HOY, EN_TRES_DIAS)

    categorias = [
        almacen.obtener("equipos", "codigo", codigo)["categoria"]
        for codigo in equipos_en_poder_de(RUT_ANA)
    ]
    assert len(categorias) == len(set(categorias)), f"categorías repetidas: {categorias}"


@pytest.mark.negativo
@pytest.mark.xfail(strict=True, reason="Defecto abierto: no se valida que las fechas sean futuras")
def test_cp52_no_se_puede_pedir_para_fechas_ya_pasadas(catalogo_amplio, sesion_ana):
    """CP-52: una solicitud con devolución en el pasado nace ya vencida.

    Además bloquea el equipo, así que inmoviliza una unidad por un préstamo
    que nunca va a ocurrir.
    """
    with pytest.raises(ErrorValidacion):
        solicitudes.crear_solicitud(
            sesion_ana, ["LAP-001"], HOY - timedelta(days=30), HOY - timedelta(days=25)
        )


@pytest.mark.borde
def test_cp53_bordes_de_duracion_del_prestamo(catalogo_amplio, sesion_ana):
    """CP-53: el mismo día y una semana exacta se aceptan; un día más, no."""
    solicitudes.crear_solicitud(sesion_ana, ["LAP-001"], HOY, HOY)
    solicitudes.crear_solicitud(
        sesion_ana, ["TAB-001"], HOY, HOY + timedelta(days=reglas.DIAS_MAX_PRESTAMO)
    )

    with pytest.raises(ErrorValidacion):
        solicitudes.crear_solicitud(
            sesion_ana, ["ARD-001"], HOY, HOY + timedelta(days=reglas.DIAS_MAX_PRESTAMO + 1)
        )


@pytest.mark.reglas
def test_cp54_no_se_puede_pedir_una_unidad_fuera_de_servicio(catalogo_amplio, sesion_ana):
    """CP-54: RF05 respeta el retiro de catálogo que hace RF03.

    Es el punto donde el trabajo de los dos integrantes se toca, así que
    conviene tener un caso que lo vigile.
    """
    equipo = almacen.obtener("equipos", "codigo", "CAM-001")
    equipo["estado"] = "fuera_de_servicio"
    almacen.reemplazar("equipos", "codigo", "CAM-001", equipo)

    with pytest.raises(ErrorDisponibilidad, match="fuera de servicio"):
        solicitudes.crear_solicitud(sesion_ana, ["CAM-001"], HOY, EN_TRES_DIAS)


@pytest.mark.negativo
def test_cp55_un_codigo_inexistente_se_rechaza(catalogo_amplio, sesion_ana):
    """CP-55: pedir algo que no existe no crea nada.

    El tipo de error es discutible: aquí llega `ErrorDisponibilidad`, mientras
    que RF04 usa `ErrorNoEncontrado` para el mismo caso. Se comprueba lo que
    importa, que es que falle y no persista nada, y la inconsistencia quedó
    anotada en la revisión del pull request.
    """
    with pytest.raises(ErrorDominio):
        solicitudes.crear_solicitud(sesion_ana, ["NO-EXISTE"], HOY, EN_TRES_DIAS)

    assert almacen.leer("solicitudes") == []
