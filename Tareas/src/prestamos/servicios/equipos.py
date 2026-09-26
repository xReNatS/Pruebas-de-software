"""RF03 - Registrar equipo y RF04 - Consultar equipo.

Cada registro de equipo es una unidad fisica, no un modelo. Varias unidades del
mismo modelo comparten nombre y categoria y se distinguen por su codigo. Esa
decision es la que permite que la disponibilidad sea una pregunta binaria por
unidad en vez de un conteo de existencias.

Criterios de aceptacion implementados:

RF03.1 Solo un encargado registra equipos; un solicitante recibe ErrorPermiso.
RF03.2 El codigo de equipo es unico. Un codigo repetido levanta ErrorDuplicado.
RF03.3 Dos unidades del mismo modelo conviven con codigos distintos y ambas
       aparecen en el catalogo.
RF03.4 Nombre y categoria son obligatorios. La categoria importa porque de ella
       depende la regla RN02 de las dos categorias distintas.
RF03.5 marcar_fuera_de_servicio exige motivo y saca la unidad del catalogo
       disponible sin borrarla.

RF04.1 Un solicitante solo ve equipos disponibles. Un encargado ve todos, con
       el estado calculado.
RF04.2 La busqueda filtra por texto libre sobre codigo, nombre y categoria, sin
       distinguir mayusculas ni acentos.
RF04.3 El detalle de un equipo no disponible indica el motivo.
RF04.4 Consultar un codigo inexistente levanta ErrorNoEncontrado.
RF04.5 El estado no se lee del JSON salvo 'fuera_de_servicio': se deriva de las
       solicitudes activas.
"""

import unicodedata

from .. import almacen, disponibilidad, modelos, registro, validaciones
from ..disponibilidad import EQUIPO_DISPONIBLE, EQUIPO_FUERA_SERVICIO
from ..errores import ErrorDuplicado, ErrorReglaNegocio
from ..sesion import Sesion


def _sin_acentos(texto: str) -> str:
    """Minusculas y sin tildes, para que 'camara' encuentre 'Cámara'.

    Se descompone en caracteres base mas diacriticos y se descartan estos
    ultimos. Es la forma mas corta de comparar texto en español sin arrastrar
    una dependencia externa.
    """
    descompuesto = unicodedata.normalize("NFKD", texto.lower())
    return "".join(caracter for caracter in descompuesto if not unicodedata.combining(caracter))


# ---------------------------------------------------------------------------
# RF03 - Registro
# ---------------------------------------------------------------------------


def registrar_equipo(
    sesion: Sesion, codigo: str, nombre: str, categoria: str, descripcion: str = ""
) -> dict:
    """Da de alta una unidad y devuelve el registro guardado."""
    sesion.exigir_encargado()

    # El codigo se normaliza igual que en la fabrica del modelo, para que la
    # comprobacion de duplicados compare lo mismo que se va a guardar.
    codigo_normalizado = validaciones.texto_obligatorio(codigo, "codigo").upper()
    if almacen.buscar("equipos", "codigo", codigo_normalizado) is not None:
        raise ErrorDuplicado(f"Ya existe un equipo con el codigo {codigo_normalizado}")

    creado = modelos.nuevo_equipo(codigo_normalizado, nombre, categoria, descripcion)
    almacen.agregar("equipos", creado)

    registro.evento(
        "equipo_registrado",
        f"Alta de equipo {creado['codigo']} ({creado['nombre']}, {creado['categoria']})",
        actor=sesion.identificador,
    )
    return creado


def marcar_fuera_de_servicio(sesion: Sesion, codigo: str, motivo: str) -> dict:
    """Retira una unidad del catalogo disponible sin borrarla del historial.

    No se permite retirar una unidad que este tomada por una solicitud activa:
    alguien la tiene en su poder o la tiene reservada, y marcarla aqui dejaria
    la solicitud apuntando a un equipo que el sistema considera inexistente.
    """
    sesion.exigir_encargado()
    motivo_limpio = validaciones.texto_obligatorio(motivo, "motivo")
    equipo = _obtener_equipo(codigo)

    if disponibilidad.esta_bloqueado(equipo["codigo"]):
        raise ErrorReglaNegocio(
            disponibilidad.motivo_no_disponible(equipo["codigo"])
            + ". Cierre o cancele esa solicitud antes de retirar el equipo."
        )

    equipo["estado"] = EQUIPO_FUERA_SERVICIO
    equipo["motivo_fuera_servicio"] = motivo_limpio
    almacen.reemplazar("equipos", "codigo", equipo["codigo"], equipo)

    registro.evento(
        "equipo_fuera_de_servicio",
        f"{equipo['codigo']} retirado del catalogo: {motivo_limpio}",
        actor=sesion.identificador,
        nivel="WARNING",
    )
    return equipo


def volver_a_servicio(sesion: Sesion, codigo: str) -> dict:
    """Reincorpora una unidad retirada. Sin esto, RF03.5 seria irreversible."""
    sesion.exigir_encargado()
    equipo = _obtener_equipo(codigo)

    if equipo.get("estado") != EQUIPO_FUERA_SERVICIO:
        raise ErrorReglaNegocio(f"El equipo {equipo['codigo']} no esta fuera de servicio")

    equipo["estado"] = EQUIPO_DISPONIBLE
    equipo.pop("motivo_fuera_servicio", None)
    almacen.reemplazar("equipos", "codigo", equipo["codigo"], equipo)

    registro.evento(
        "equipo_en_servicio",
        f"{equipo['codigo']} reincorporado al catalogo",
        actor=sesion.identificador,
    )
    return equipo


# ---------------------------------------------------------------------------
# RF04 - Consulta
# ---------------------------------------------------------------------------


def buscar_equipos(sesion: Sesion, texto: str = "", solo_disponibles: bool = False) -> list[dict]:
    """Catalogo filtrado por texto y por rol.

    Un solicitante nunca ve unidades ocupadas ni retiradas, aunque pase
    solo_disponibles en False: el filtro por rol manda sobre el argumento.
    """
    if sesion.es_solicitante:
        solo_disponibles = True

    aguja = _sin_acentos(texto.strip())
    bloqueos = disponibilidad.bloqueos_por_equipo()
    resultado = []

    for equipo in almacen.leer("equipos"):
        if solo_disponibles and not disponibilidad.esta_disponible(equipo, bloqueos):
            continue
        if aguja and not _coincide(equipo, aguja):
            continue
        resultado.append(_con_estado_calculado(equipo, bloqueos))

    return sorted(resultado, key=lambda e: e["codigo"])


def _coincide(equipo: dict, aguja: str) -> bool:
    """RF04.2 - el texto se busca en codigo, nombre y categoria."""
    campos = (equipo["codigo"], equipo["nombre"], equipo["categoria"])
    return any(aguja in _sin_acentos(campo) for campo in campos)


def detalle_equipo(sesion: Sesion, codigo: str) -> dict:
    """Ficha de una unidad, con el motivo si no se puede pedir.

    El detalle por codigo funciona para cualquiera de los dos roles, incluso
    sobre una unidad ocupada. La restriccion del solicitante es que no la vea
    listada como opcion, no que no pueda averiguar por que no esta disponible:
    saber hasta cuando esta tomada le sirve para volver a intentarlo.
    """
    equipo = _obtener_equipo(codigo)
    ficha = _con_estado_calculado(equipo)
    ficha["motivo_no_disponible"] = disponibilidad.motivo_no_disponible(equipo["codigo"])
    return ficha


def _obtener_equipo(codigo: str) -> dict:
    """Busca por codigo normalizado. RF04.4 - inexistente levanta ErrorNoEncontrado."""
    codigo_normalizado = validaciones.texto_obligatorio(codigo, "codigo").upper()
    return almacen.obtener("equipos", "codigo", codigo_normalizado)


def _con_estado_calculado(equipo: dict, bloqueos: dict | None = None) -> dict:
    """RF04.5 - el estado mostrado se deriva, no se lee del archivo.

    Se devuelve una copia para que quien reciba la ficha no pueda modificar sin
    querer el registro que despues se escribe en disco.
    """
    ficha = dict(equipo)
    ficha["estado"] = disponibilidad.estado_calculado(equipo, bloqueos)
    return ficha
