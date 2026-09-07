# Matriz de trazabilidad

Los identificadores son los mismos en el documento, el código, las pruebas y los
Issues. La columna Resultado se completa al ejecutar la suite y se actualiza en
cada entrega parcial.

Estado actual: RF01 a RF07 y RF09 implementados y verificados, más la
infraestructura de log de eventos e integración con Sentry. RF08, RF10 y RF11
tienen sus casos de prueba escritos y marcados como `xfail` a la espera de su
implementación.

La prueba cruzada de RF05 encontró tres defectos. Los dos de severidad alta,
#27 y #28, ya están corregidos y reejecutados: los casos CP-50 y CP-51 pasan.
Queda abierto #29, de severidad media, con su caso CP-52 marcado
`xfail(strict=True)`; cuando se corrija, el caso pasará y `strict` obligará a
quitar la marca.

**Nota sobre la cobertura parcial de RF02, RF03 y RF04.** Los casos CP-16 a
CP-23 cubren el camino principal de cada requerimiento, pero varios criterios
quedaron sin caso automatizado a propósito: su diseño le corresponde al
integrante que hace la prueba cruzada, según el Issue #14. Se comprobaron de
forma manual al implementar y todos se cumplen, pero mientras no exista el
caso, ninguno de los tres puede declararse cerrado en el informe.

| Requerimiento | Criterios cubiertos por un caso | Criterios verificados solo a mano |
| --- | --- | --- |
| RF02 | RF02.1, RF02.2 | RF02.3 dígito verificador, RF02.4 contraseña como hash, RF02.5 correo único entre colecciones, RF02.6 evento de cambio de estado |
| RF03 | RF03.2, RF03.3, RF03.4 | RF03.1 permiso, RF03.5 retiro del catálogo con motivo |
| RF04 | RF04.1 | RF04.2 búsqueda sin acentos, RF04.3 motivo en el detalle, RF04.4 código inexistente, RF04.5 estado derivado |

| ID | Criterio de aceptación | Evidencia de implementación | Casos de prueba | Resultado |
| --- | --- | --- | --- | --- |
| RF01 | Con credenciales válidas se obtiene una sesión con el rol correcto; con credenciales inválidas se levanta `ErrorAutenticacion` con un mensaje que no revela si el correo existe | `servicios/autenticacion.py` | CP-01, CP-02, CP-03, CP-04, CP-05 | Aprobado |
| RF02 | Solo un encargado registra personas; RUT y correo son únicos; la contraseña se guarda como hash | `servicios/personas.py` | CP-16, CP-17, CP-18 | Aprobado (cobertura parcial, ver nota) |
| RF03 | Solo un encargado registra equipos; el código es único; dos unidades del mismo modelo conviven con códigos distintos | `servicios/equipos.py` | CP-19, CP-20, CP-21, CP-22 | Aprobado (cobertura parcial, ver nota) |
| RF04 | El solicitante ve solo equipos disponibles; el encargado ve todos con su estado calculado; un código inexistente levanta `ErrorNoEncontrado` | `servicios/equipos.py` | CP-23, CP-13 | Aprobado (cobertura parcial, ver nota) |
| RF05 | La solicitud nace en `por_revisar` con 1 o 2 equipos de categorías distintas, dentro del máximo de 7 días y sobre equipos disponibles | `servicios/solicitudes.py` | CP-24 a CP-31, CP-53, CP-54, CP-55 | Aprobado. Queda abierto #29, de severidad media |
| RF06 | El solicitante ve solo sus solicitudes; el encargado filtra por vigentes, futuras y atrasadas, y el atraso se calcula por fecha | `servicios/solicitudes.py` | CP-32, CP-62 | Aprobado |
| RF07 | Solo el encargado aprueba o rechaza y solo desde `por_revisar`; el rechazo exige motivo; al aprobar se revalida la disponibilidad | `servicios/solicitudes.py` | CP-32, CP-33, CP-60, CP-61 | Aprobado |
| RF08 | Solo el encargado registra entregas y confirma devoluciones; al concluir desde `atrasada` el solicitante queda `pendiente`; la unidad se libera | `servicios/prestamos.py` | CP-35, CP-37, CP-38 | Pendiente |
| RF09 | El solicitante cancela solo sus solicitudes, y solo en `por_revisar` o `aprobada`; el encargado también puede, con motivo obligatorio; los equipos se liberan de inmediato | `servicios/solicitudes.py` | CP-34, CP-12, CP-56 a CP-59 | Aprobado |
| RF10 | El solicitante declara la devolución, incluso antes del vencimiento, y esa declaración por sí sola no libera la unidad | `servicios/prestamos.py` | CP-35, CP-38 | Pendiente |
| RF11 | Se renueva solo desde `periodo_gracia`, una única vez y por hasta 7 días | `servicios/prestamos.py` | CP-36 | Pendiente |
| RN01 | Un solicitante no puede tener más de 2 equipos simultáneamente, sumando todas sus solicitudes activas | `servicios/solicitudes.py` | CP-50 | Aprobado tras corregir #27 |
| RN02 | Los equipos en poder de una persona son de categorías distintas, aunque vengan de solicitudes separadas | `servicios/solicitudes.py` | CP-51 | Aprobado tras corregir #28 |
| RN16 | Los límites se aplican sobre la suma de las solicitudes activas, no sobre cada una por separado | `servicios/solicitudes.py` | CP-50, CP-51 | Aprobado |
| RN12 | Toda solicitud activa bloquea sus equipos, incluida una que aún está por revisar | `disponibilidad.py` | CP-10, CP-11, CP-12, CP-13, CP-54 | Aprobado |
| RN15 | Las transiciones fuera de la tabla y las ejecutadas por un rol no autorizado fallan | `estados.py` | CP-06, CP-07, CP-08, CP-09 | Aprobado |
| VAL01 | Un RUT con dígito verificador incorrecto o formato inválido es rechazado antes de tocar el disco | `validaciones.py` | CP-14, CP-15 | Aprobado |
| INF01 | Todo evento relevante queda en el log con su actor, y un defecto inesperado se convierte en mensaje sin tumbar la aplicación | `registro.py`, `cli/comun.py` | CP-40, CP-41, CP-43 | Aprobado |
| INF02 | Los errores previstos del negocio no se reportan a Sentry, y la suite nunca envía eventos al panel real | `registro.py`, `config.py` | CP-39, CP-42 | Aprobado |
| INF03 | Un defecto real llega a Sentry con traza, variables locales, migas de pan y el commit que lo produjo | `registro.py` | Verificación manual, ver `evidencias/sentry/` | Aprobado |
| DEM01 | El escenario de demostración incluye un ejemplo de cada estado de solicitud y de equipo, y un solicitante bloqueado por atraso | `demo.py` | CP-45, CP-46, CP-47 | Aprobado |
| DEM02 | La demostración es reproducible con un comando y el guion no se desactualiza en silencio | `demo.py`, `docs/guion-demostracion.md` | CP-44, CP-48, CP-49 | Aprobado |

## Cobertura por categoría exigida

| Categoría | Mínimo pedido | Casos |
| --- | --- | --- |
| Funcionales | 5 | CP-01, CP-02, CP-06, CP-10, CP-12, CP-16, CP-19, CP-23, CP-24, CP-32, CP-40, CP-45, CP-46 |
| De borde | 4 | CP-04, CP-09, CP-14, CP-20, CP-27, CP-28, CP-36, CP-43, CP-44, CP-48 |
| Negativos o con entradas inválidas | 3 | CP-03, CP-05, CP-07, CP-08, CP-13, CP-15, CP-17, CP-18, CP-21, CP-22, CP-25, CP-33, CP-34, CP-39, CP-41, CP-42, CP-49 |
| Que combinan reglas | 2 | CP-11, CP-26, CP-29, CP-30, CP-31, CP-35, CP-37, CP-47 |
| Escenario completo | 1 | CP-38 |

Las categorías están declaradas como marcas de pytest, de modo que el recuento
se puede reproducir desde la línea de comando:

```bash
python -m pytest -m borde --collect-only -q
```
