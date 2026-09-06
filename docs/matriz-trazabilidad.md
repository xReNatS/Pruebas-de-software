# Matriz de trazabilidad

Los identificadores son los mismos en el documento, el código, las pruebas y los
Issues. La columna Resultado se completa al ejecutar la suite y se actualiza en
cada entrega parcial.

Estado actual: RF01 a RF04 implementados. RF05 a RF11 tienen sus casos de
prueba escritos y marcados como `xfail` a la espera de su implementación.

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
| RF05 | La solicitud nace en `por_revisar` con 1 o 2 equipos de categorías distintas, dentro del máximo de 7 días y sobre equipos disponibles | `servicios/solicitudes.py` | CP-24, CP-25, CP-26, CP-27, CP-28, CP-29, CP-30, CP-31 | Pendiente |
| RF06 | El solicitante ve solo sus solicitudes; el encargado filtra por vigentes, futuras y atrasadas, y el atraso se calcula por fecha | `servicios/solicitudes.py` | CP-32 | Pendiente |
| RF07 | Solo el encargado aprueba o rechaza y solo desde `por_revisar`; el rechazo exige motivo; al aprobar se revalida la disponibilidad | `servicios/solicitudes.py` | CP-32, CP-33 | Pendiente |
| RF08 | Solo el encargado registra entregas y confirma devoluciones; al concluir desde `atrasada` el solicitante queda `pendiente`; la unidad se libera | `servicios/prestamos.py` | CP-35, CP-37, CP-38 | Pendiente |
| RF09 | El solicitante cancela solo sus solicitudes, y solo en `por_revisar` o `aprobada`; los equipos se liberan de inmediato | `servicios/solicitudes.py` | CP-34, CP-12 | Pendiente |
| RF10 | El solicitante declara la devolución, incluso antes del vencimiento, y esa declaración por sí sola no libera la unidad | `servicios/prestamos.py` | CP-35, CP-38 | Pendiente |
| RF11 | Se renueva solo desde `periodo_gracia`, una única vez y por hasta 7 días | `servicios/prestamos.py` | CP-36 | Pendiente |
| RN12 | Toda solicitud activa bloquea sus equipos, incluida una que aún está por revisar | `disponibilidad.py` | CP-10, CP-11, CP-12, CP-13 | Aprobado |
| RN15 | Las transiciones fuera de la tabla y las ejecutadas por un rol no autorizado fallan | `estados.py` | CP-06, CP-07, CP-08, CP-09 | Aprobado |
| VAL01 | Un RUT con dígito verificador incorrecto o formato inválido es rechazado antes de tocar el disco | `validaciones.py` | CP-14, CP-15 | Aprobado |

## Cobertura por categoría exigida

| Categoría | Mínimo pedido | Casos |
| --- | --- | --- |
| Funcionales | 5 | CP-01, CP-02, CP-06, CP-10, CP-12, CP-16, CP-19, CP-23, CP-24, CP-32 |
| De borde | 4 | CP-04, CP-09, CP-14, CP-20, CP-27, CP-28, CP-36 |
| Negativos o con entradas inválidas | 3 | CP-03, CP-05, CP-07, CP-08, CP-13, CP-15, CP-17, CP-18, CP-21, CP-22, CP-25, CP-33, CP-34 |
| Que combinan reglas | 2 | CP-11, CP-26, CP-29, CP-30, CP-31, CP-35, CP-37 |
| Escenario completo | 1 | CP-38 |

Las categorías están declaradas como marcas de pytest, de modo que el recuento
se puede reproducir desde la línea de comando:

```bash
python -m pytest -m borde --collect-only -q
```
