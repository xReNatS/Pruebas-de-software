# Reglas de negocio, alcance y exclusiones

Cada regla tiene un identificador estable. Ese identificador se usa en los
Issues, en los mensajes de commit, en los casos de prueba y en la matriz de
trazabilidad. Las constantes viven en `src/prestamos/reglas.py`.

## Reglas

| ID | Regla | Dónde vive en el código |
| --- | --- | --- |
| RN01 | Un solicitante puede tener como máximo 2 equipos simultáneamente | `reglas.MAX_EQUIPOS_SIMULTANEOS` |
| RN02 | Los equipos en poder de una persona deben ser de categorías distintas | `reglas.CATEGORIAS_DEBEN_SER_DISTINTAS` |
| RN03 | Una solicitud incluye 1 o 2 equipos | `reglas.MIN/MAX_EQUIPOS_POR_SOLICITUD` |
| RN04 | La duración máxima de un préstamo es de 1 semana | `reglas.DIAS_MAX_PRESTAMO` |
| RN05 | Tras la aprobación hay 2 días para retirar; si no, se cancela | `reglas.DIAS_PARA_RETIRO` |
| RN06 | Hay 1 día de gracia tras el vencimiento antes de marcar atraso | `reglas.DIAS_PERIODO_GRACIA` |
| RN07 | Se permite una sola renovación, de hasta 1 semana | `reglas.MAX_RENOVACIONES`, `reglas.DIAS_MAX_RENOVACION` |
| RN08 | Las cuentas son separadas: un correo es solicitante o encargado, nunca ambos | `servicios.autenticacion` |
| RN09 | Solo los solicitantes generan solicitudes | `servicios.solicitudes.crear_solicitud` |
| RN10 | Un solicitante con 2 equipos en su poder no puede crear nuevas solicitudes | `servicios.solicitudes.crear_solicitud` |
| RN11 | Quien no devuelve a tiempo queda en estado `pendiente` y no puede pedir más | `servicios.prestamos.actualizar_estados_por_fecha` |
| RN12 | Un equipo tomado por una solicitud activa no se puede reservar | `disponibilidad.esta_disponible` |
| RN13 | El solicitante puede devolver antes de tiempo | `servicios.prestamos.declarar_devolucion` |
| RN14 | Estudiantes y profesores se rigen por los mismos límites | No hay distinción de subtipo en el modelo |
| RN15 | El estado `atrasada` lo calcula el sistema por fecha, nunca una persona | `estados.TRANSICIONES`, rol `sistema` |
| RN16 | Un solicitante puede tener varias solicitudes activas, pero los límites de RN01 y RN02 se aplican sobre la suma de todas ellas, no sobre cada una por separado | `servicios.solicitudes.crear_solicitud` |

## Alcance: lo que el sistema sí hace

- Registro y consulta de personas autorizadas, solicitantes y encargados.
- Registro y consulta de equipos, con varias unidades por modelo.
- Autenticación con dos roles y contraseñas almacenadas como hash.
- Creación de solicitudes de reserva o préstamo de uno o dos equipos.
- Aprobación y rechazo de solicitudes por parte del encargado.
- Registro de entregas, devoluciones y cancelaciones.
- Consulta de préstamos vigentes, futuros y atrasados.
- Cálculo de disponibilidad de equipos derivado de las solicitudes activas.
- Persistencia en archivos JSON, log de eventos y datos de demostración.

## Exclusiones: lo que el sistema explícitamente no hace

- Multas, cobros o sanciones económicas.
- Historial de mantenimiento o reparación de equipos.
- Interfaz gráfica o web. Solo línea de comando.
- Autorregistro de usuarios y recuperación de contraseña. Las cuentas las crea
  siempre un encargado.
- Gestión física de inventario: ubicaciones, bodegas o stock por sede.
- Notificaciones por correo o mensajería.
- Reserva por rango de fechas con liberación automática. Un equipo tomado
  queda bloqueado hasta que la solicitud se cierra.
- Solicitudes simultáneas de la misma categoría separadas por fechas. El
  cliente lo mencionó, pero es incompatible con la decisión de bloquear desde
  el registro. La divergencia está documentada en `supuestos.md`, punto A13.

## Requerimientos funcionales

| ID | Requerimiento | Rol | Módulo |
| --- | --- | --- | --- |
| RF01 | Inicio de sesión | ambos | `servicios/autenticacion.py` |
| RF02 | Registrar persona autorizada | encargado | `servicios/personas.py` |
| RF03 | Registrar equipo | encargado | `servicios/equipos.py` |
| RF04 | Consultar equipo | ambos | `servicios/equipos.py` |
| RF05 | Crear solicitud | solicitante | `servicios/solicitudes.py` |
| RF06 | Consultar solicitudes | ambos | `servicios/solicitudes.py` |
| RF07 | Aprobar o rechazar solicitud | encargado | `servicios/solicitudes.py` |
| RF08 | Registrar entrega y confirmar devolución | encargado | `servicios/prestamos.py` |
| RF09 | Cancelar solicitud | solicitante | `servicios/solicitudes.py` |
| RF10 | Declarar devolución | solicitante | `servicios/prestamos.py` |
| RF11 | Renovar el préstamo | solicitante | `servicios/prestamos.py` |

## Semántica de los filtros de RF06

La definición inicial de los filtros dejaba solicitudes fuera de todo filtro y
se ajustó al implementar. Esta es la definición vigente, que es la que el código
aplica y la que verifican los casos CP-62 y CP-32.

| Filtro | Qué incluye | Por qué |
| --- | --- | --- |
| `todas` | Todo lo visible para el rol | — |
| `mias` | Solo las del solicitante de la sesión | Lo usa el menú del solicitante |
| `vigentes` | `en_prestamo`, `periodo_gracia` y `atrasada` | Son los estados en que la persona tiene el equipo físicamente. Un préstamo atrasado sigue vigente para el laboratorio: el equipo está afuera |
| `futuras` | `por_revisar` y `aprobada`, sin mirar la fecha | Una solicitud aprobada cuya fecha de retiro ya pasó pero que nadie retiró sigue siendo trabajo por delante. Filtrar por fecha la habría dejado invisible en todos los filtros |
| `atrasadas` | `atrasada`, más cualquier solicitud activa cuya fecha de devolución ya venció | Se calcula por fecha y no leyendo un campo, así un atraso aparece apenas ocurre sin reescribir la solicitud |

**`vigentes` y `atrasadas` se solapan a propósito.** Una solicitud atrasada
aparece en ambos, porque responde a dos preguntas distintas: qué equipos están
afuera, y a quién hay que reclamarle.
