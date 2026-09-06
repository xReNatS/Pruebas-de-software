"""Constantes de las reglas de negocio.

Cada constante tiene un unico lugar de definicion para que las pruebas
puedan referenciarla en vez de repetir numeros magicos. Si el cliente
cambia una regla, se cambia aqui y las pruebas siguen siendo validas.
"""

# RN01 - Un solicitante puede tener a lo mas 2 equipos simultaneamente.
MAX_EQUIPOS_SIMULTANEOS = 2

# RN02 - Los equipos en poder de una persona deben ser de categorias distintas.
CATEGORIAS_DEBEN_SER_DISTINTAS = True

# RN03 - Una solicitud incluye 1 o 2 equipos.
MIN_EQUIPOS_POR_SOLICITUD = 1
MAX_EQUIPOS_POR_SOLICITUD = 2

# RN04 - Duracion maxima de un prestamo: 1 semana.
DIAS_MAX_PRESTAMO = 7

# RN05 - Tras la aprobacion hay 2 dias para retirar; si no, se cancela.
DIAS_PARA_RETIRO = 2

# RN06 - Periodo de gracia tras el vencimiento antes de marcar atraso.
# Decision de equipo: el enunciado interno decia 1 dia en Reglas de Negocio
# y 2 dias en la seccion de ambiguedades. Se adopta 1 dia (ver docs/supuestos.md).
DIAS_PERIODO_GRACIA = 1

# RN07 - Como maximo una renovacion, de hasta 1 semana adicional.
MAX_RENOVACIONES = 1
DIAS_MAX_RENOVACION = 7

# Estados del solicitante.
SOLICITANTE_AL_DIA = "al_dia"
SOLICITANTE_PENDIENTE = "pendiente"

# Roles del sistema. RN08 - las cuentas son separadas: un correo es
# solicitante o encargado, nunca ambos.
ROL_SOLICITANTE = "solicitante"
ROL_ENCARGADO = "encargado"
