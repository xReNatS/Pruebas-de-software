# Evidencia de la integración con Sentry

Verificación de punta a punta del Issue #12. No es una prueba de que el código
compile: es la comprobación de que un defecto real, provocado a propósito,
recorre todo el camino hasta el panel de Sentry.

| Dato | Valor |
| --- | --- |
| Issue en Sentry | 7715896391 |
| Proyecto | pruebas-de-software |
| Fecha | 2026-09-06 21:09:57 UTC |
| Excepción | `JSONDecodeError: Expecting property name enclosed in double quotes` |
| Origen | `prestamos.almacen` en `leer` |
| Commit asociado | `059aa8b` |
| Entorno | desarrollo |

Archivos: [`evento-7715896391-crudo.md`](evento-7715896391-crudo.md) con el
volcado completo del evento, y
[`traza-jsondecodeerror.png`](traza-jsondecodeerror.png) con la captura del
panel.

## Cómo se provocó

Se escribió un `data/equipos.json` truncado, con una llave sin cerrar:

```
[{"codigo": "LAP-001",
```

Luego se entró a la aplicación como encargado y se pidió el catálogo de
equipos, que es la operación que lee ese archivo.

Es reproducible: basta con corromper el archivo, ejecutar `.\make.ps1 correr`,
entrar con un encargado y elegir la opción de catálogo.

## Qué demuestra la evidencia

**La aplicación no se cae.** El tag `handled: yes` confirma que la excepción
fue atrapada. El usuario vio el mensaje "Ocurrió un error inesperado" y siguió
operando; el proceso terminó con código 0.

**El defecto llega con la traza completa hasta nuestro código.** La pila
muestra el recorrido desde `cli/comun.py` en `ejecutar`, pasando por
`servicios/equipos.py` en `buscar_equipos`, hasta `almacen.py` en `leer`, que
es donde de verdad ocurre. Sentry marca qué marcos son de la aplicación y
cuáles de la biblioteca estándar.

**Llegan las variables locales de cada marco.** En la captura se ve `actor` con
valor `ENC-0001` y `fallo` con el mensaje exacto. Eso es lo que permite
diagnosticar sin pedirle al usuario que reproduzca el problema.

**Llegan las migas de pan.** El evento incluye el ingreso del encargado que
ocurrió justo antes:

```
[info]  prestamos: Ingreso de encargado    {'actor': 'ENC-0001', 'evento': 'login_exitoso'}
[error] prestamos: JSONDecodeError: ...    {'actor': 'ENC-0001', 'evento': 'error_inesperado'}
```

Es la consecuencia directa de dejar `LoggingIntegration(level=INFO)` activa
para migas de pan pero con `event_level=None` para no duplicar eventos.

**El evento queda atado a un commit.** El tag `release` trae el hash
`059aa8b`, así que se puede saber exactamente con qué versión del código
ocurrió. Eso es trazabilidad real entre un fallo en ejecución y el
repositorio.

**El actor queda identificado sin datos personales.** El campo `User.ID` es
`ENC-0001`, el identificador interno del encargado. No se envía nombre ni
correo, porque el SDK se inicializa con `send_default_pii=False`.

## Limitación detectada

El evento incluye el tag `server_name` con el nombre del equipo desde el que se
ejecutó. `send_default_pii=False` no lo cubre, porque Sentry no lo considera
dato personal. En un despliegue real convendría eliminarlo con un `before_send`
si el nombre del host revelara algo de la infraestructura. Para este trabajo se
deja como está y queda declarado aquí.

## Lo que esta evidencia no cubre

No se comprueba automáticamente que el evento llegue al panel: eso exigiría red
y un DSN real en cada ejecución de la suite. Lo que sí está automatizado son
los casos CP-39 a CP-43, que cubren la parte bajo nuestro control: que un error
previsto nunca se reporte, que un defecto inesperado quede registrado sin
tumbar la aplicación, y que la suite no envíe eventos al panel real.
