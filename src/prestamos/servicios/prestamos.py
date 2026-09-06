"""RF08 - Registrar devolucion (encargado), RF10 - Realizar devolucion
(solicitante) y RF11 - Renovar el prestamo. Incluye la entrega y las
transiciones automaticas por fecha.

Responsable: integrante B. Estado: pendiente de implementacion.

Modelado de la devolucion, decision del equipo: RF10 y RF08 son los dos lados
del mismo hecho fisico. El solicitante declara la devolucion (RF10), lo que
solo escribe la marca devolucion_declarada_en; el equipo queda liberado
unicamente cuando el encargado confirma la recepcion (RF08) y la solicitud
pasa a 'concluida'. Asi la maquina de estados no necesita un estado extra.

Contrato esperado y criterios de aceptacion:

RF08.1 Solo un encargado confirma devoluciones.
RF08.2 Se puede concluir desde 'en_prestamo', 'periodo_gracia' y 'atrasada';
       desde cualquier otro estado se levanta ErrorTransicion.
RF08.3 Al concluir desde 'atrasada' el solicitante queda en estado 'pendiente'.
RF08.4 Al concluir, los equipos vuelven a estar disponibles.
RF08.5 La confirmacion queda registrada en el log con el actor encargado.

RF10.1 Solo el dueno de la solicitud puede declarar su devolucion.
RF10.2 Se permite declarar antes del vencimiento (devolucion anticipada).
RF10.3 Declarar no libera el equipo por si solo; hasta que RF08 confirme, la
       solicitud sigue activa y el equipo sigue bloqueado.

RF11.1 Solo se renueva estando en 'periodo_gracia'.
RF11.2 Como maximo reglas.MAX_RENOVACIONES renovacion, de hasta
       reglas.DIAS_MAX_RENOVACION dias; una segunda intentona levanta
       ErrorReglaNegocio.
RF11.3 Al renovar, la solicitud vuelve a 'en_prestamo' con nueva fecha de
       devolucion y el contador de renovaciones sube en uno.

Transiciones automaticas (ejecutadas por el sistema, no por una persona):
  en_prestamo    -> periodo_gracia  al pasar la fecha de devolucion
  periodo_gracia -> atrasada        al pasar reglas.DIAS_PERIODO_GRACIA
  aprobada       -> cancelada       si no se retira en reglas.DIAS_PARA_RETIRO
"""

from datetime import date

from ..sesion import Sesion


def registrar_entrega(sesion: Sesion, identificador: str) -> dict:
    """Encargado entrega fisicamente los equipos: aprobada -> en_prestamo."""
    raise NotImplementedError("RF08: registrar entrega")


def declarar_devolucion(sesion: Sesion, identificador: str) -> dict:
    raise NotImplementedError("RF10: declarar devolucion (solicitante)")


def confirmar_devolucion(sesion: Sesion, identificador: str, observacion: str = "") -> dict:
    raise NotImplementedError("RF08: confirmar devolucion (encargado)")


def renovar_prestamo(sesion: Sesion, identificador: str, dias: int) -> dict:
    raise NotImplementedError("RF11: renovar prestamo")


def actualizar_estados_por_fecha(hoy: date | None = None) -> list[dict]:
    """Aplica las transiciones automaticas y devuelve las solicitudes tocadas.

    Se llama al iniciar la aplicacion y desde las pruebas con una fecha fija,
    de manera que el paso del tiempo sea reproducible.
    """
    raise NotImplementedError("RF08/RF11: transiciones automaticas por fecha")
