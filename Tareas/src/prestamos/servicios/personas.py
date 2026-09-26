"""RF02 - Registrar persona autorizada (solicitantes y encargados).

No hay autorregistro: las cuentas las crea siempre un encargado. Esa fue una
decision de alcance, documentada en docs/reglas-de-negocio.md.

Criterios de aceptacion implementados:

RF02.1 Solo un encargado autenticado puede registrar personas. Con una sesion
       de solicitante se levanta ErrorPermiso.
RF02.2 El RUT y el correo son unicos. Un duplicado levanta ErrorDuplicado y no
       modifica el archivo JSON.
RF02.3 Un RUT con digito verificador incorrecto levanta ErrorValidacion antes
       de tocar el disco.
RF02.4 La contrasena nunca se guarda en texto plano: el JSON solo contiene
       contrasena_hash.
RF02.5 Un correo no puede existir a la vez en solicitantes y encargados, porque
       las cuentas son separadas (RN08).
RF02.6 Cada registro y cada cambio de estado dejan un evento en el log.
"""

from .. import almacen, modelos, registro, validaciones
from ..errores import ErrorDuplicado, ErrorNoEncontrado, ErrorValidacion
from ..reglas import SOLICITANTE_AL_DIA, SOLICITANTE_PENDIENTE
from ..sesion import Sesion

ESTADOS_SOLICITANTE = (SOLICITANTE_AL_DIA, SOLICITANTE_PENDIENTE)


def _exigir_correo_libre(correo: str) -> None:
    """RF02.5 - el correo no puede estar tomado en ninguna de las dos colecciones.

    Se comprueba contra ambas y no solo contra la coleccion de destino, porque
    el inicio de sesion busca por correo en las dos: un correo repetido haria
    que el rol de la sesion dependiera del orden de busqueda.
    """
    if almacen.buscar("encargados", "correo", correo) is not None:
        raise ErrorDuplicado(f"El correo {correo} ya esta registrado como encargado")
    if almacen.buscar("solicitantes", "correo", correo) is not None:
        raise ErrorDuplicado(f"El correo {correo} ya esta registrado como solicitante")


def registrar_solicitante(
    sesion: Sesion, nombre: str, rut: str, correo: str, contrasena: str
) -> dict:
    """Da de alta un solicitante y devuelve el registro guardado.

    El orden de las comprobaciones importa: primero el permiso, luego el
    formato de los datos y al final la unicidad. Asi una sesion sin permiso
    recibe siempre ErrorPermiso, aunque ademas los datos sean invalidos.
    """
    sesion.exigir_encargado()

    # Se normaliza antes de comparar: sin esto, "ANA@Lab.cl" y "ana@lab.cl"
    # pasarian como correos distintos y romperian el inicio de sesion.
    rut_normalizado = validaciones.rut(rut)
    correo_normalizado = validaciones.correo(correo)

    if almacen.buscar("solicitantes", "rut", rut_normalizado) is not None:
        raise ErrorDuplicado(f"Ya existe un solicitante con el RUT {rut_normalizado}")
    _exigir_correo_libre(correo_normalizado)

    creado = modelos.nuevo_solicitante(nombre, rut_normalizado, correo_normalizado, contrasena)
    almacen.agregar("solicitantes", creado)

    registro.evento(
        "solicitante_registrado",
        f"Alta de solicitante {creado['nombre']} ({creado['rut']})",
        actor=sesion.identificador,
    )
    return creado


def registrar_encargado(sesion: Sesion, nombre: str, correo: str, contrasena: str) -> dict:
    """Da de alta otro encargado. El identificador se asigna solo, tipo ENC-0003."""
    sesion.exigir_encargado()

    correo_normalizado = validaciones.correo(correo)
    _exigir_correo_libre(correo_normalizado)

    identificador = almacen.siguiente_id("encargados", "ENC")
    creado = modelos.nuevo_encargado(identificador, nombre, correo_normalizado, contrasena)
    almacen.agregar("encargados", creado)

    registro.evento(
        "encargado_registrado",
        f"Alta de encargado {creado['nombre']} ({creado['id']})",
        actor=sesion.identificador,
    )
    return creado


def listar_solicitantes(sesion: Sesion) -> list[dict]:
    """Listado para el encargado, ordenado por nombre y sin el hash de contrasena."""
    sesion.exigir_encargado()
    personas = sorted(almacen.leer("solicitantes"), key=lambda p: p["nombre"].lower())
    return [_sin_credenciales(persona) for persona in personas]


def listar_encargados(sesion: Sesion) -> list[dict]:
    sesion.exigir_encargado()
    personas = sorted(almacen.leer("encargados"), key=lambda p: p["nombre"].lower())
    return [_sin_credenciales(persona) for persona in personas]


def _sin_credenciales(persona: dict) -> dict:
    """Copia del registro sin el hash, para que no llegue a la interfaz ni a los logs."""
    return {clave: valor for clave, valor in persona.items() if clave != "contrasena_hash"}


def cambiar_estado_solicitante(sesion: Sesion, rut: str, estado: str) -> dict:
    """Pasa a 'pendiente' o devuelve a 'al_dia' por decision de un encargado."""
    sesion.exigir_encargado()
    return _fijar_estado(rut, estado, actor=sesion.identificador)


def marcar_estado_por_sistema(rut: str, estado: str) -> dict:
    """Igual que la anterior, pero sin sesion, para las transiciones automaticas.

    La usa RF08 cuando el vencimiento del periodo de gracia deja al solicitante
    en estado 'pendiente' (RN11). Ese cambio no lo decide una persona, asi que
    no puede exigir una sesion.
    """
    return _fijar_estado(rut, estado, actor="sistema")


def _fijar_estado(rut: str, estado: str, actor: str) -> dict:
    if estado not in ESTADOS_SOLICITANTE:
        raise ErrorValidacion(
            f"Estado de solicitante invalido: {estado}. "
            f"Valores permitidos: {', '.join(ESTADOS_SOLICITANTE)}"
        )

    rut_normalizado = validaciones.rut(rut)
    persona = almacen.buscar("solicitantes", "rut", rut_normalizado)
    if persona is None:
        raise ErrorNoEncontrado(f"No existe un solicitante con el RUT {rut_normalizado}")

    anterior = persona["estado"]
    if anterior == estado:
        return persona

    persona["estado"] = estado
    almacen.reemplazar("solicitantes", "rut", rut_normalizado, persona)

    registro.evento(
        "estado_solicitante_cambiado",
        f"{rut_normalizado} paso de '{anterior}' a '{estado}'",
        actor=actor,
        nivel="WARNING" if estado == SOLICITANTE_PENDIENTE else "INFO",
    )
    return persona
