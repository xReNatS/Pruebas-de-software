# Sistema de préstamo de equipos de laboratorio

Aplicación de línea de comando para gestionar el préstamo de equipos
tecnológicos de un laboratorio universitario: registro de personas y equipos,
solicitudes de préstamo, aprobación, entrega, devolución y consulta de préstamos
vigentes, futuros y atrasados.

Proyecto del ramo Pruebas de Software. El énfasis está en las reglas de negocio
explícitas, la verificación automatizada y la trazabilidad entre requerimiento,
código y caso de prueba.

## Tecnologías

- Python 3.11 o superior, solo biblioteca estándar para el dominio.
- Persistencia en archivos JSON. No hay base de datos.
- pytest para las pruebas.
- python-dotenv para la configuración y sentry-sdk para el reporte de errores.

## Atajos: `make` y `make.ps1`

El proyecto trae un `Makefile` y un `make.ps1` con los mismos objetivos, así que
no hace falta recordar comandos largos. En Windows se usa el script, que no
requiere instalar nada. En Linux o macOS se usa `make`.

| Objetivo | Qué hace |
| --- | --- |
| `instalar` | Crea el entorno virtual e instala las dependencias |
| `correr` | Inicia la aplicación |
| `probar` | Ejecuta toda la suite de pruebas |
| `verificar` | Ejecuta la suite y muestra el recuento de casos por categoría |
| `probar-funcional`, `probar-borde`, `probar-negativo`, `probar-reglas`, `probar-escenario` | Ejecuta solo esa categoría de casos |
| `probar-pendientes` | Lista los casos que esperan la implementación de su requerimiento |
| `evidencia` | Guarda la salida de las pruebas en `evidencias/` con la fecha |
| `demo` | Regenera los datos de demostración |
| `reiniciar` | Borra datos y logs, y vuelve a cargar la demostración |
| `registro` | Muestra las últimas líneas del log de eventos |
| `limpiar` | Borra cachés, logs y archivos temporales |

Arranque completo en Windows:

```powershell
.\make.ps1 instalar
.\make.ps1 probar
.\make.ps1 correr
```

Lo mismo en Linux o macOS:

```bash
make instalar
make probar
make correr
```

Ejecutar `.\make.ps1` o `make` sin argumentos muestra la lista de objetivos y
qué intérprete de Python se está usando.

Si PowerShell bloquea el script por la política de ejecución, se destraba solo
para la sesión actual:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Los objetivos usan el entorno virtual en cuanto existe, sin que haga falta
activarlo a mano. La instalación manual que sigue es equivalente y está por si
alguien prefiere hacerlo paso a paso.

## Instalación

```bash
git clone https://github.com/xReNatS/Pruebas-de-software.git
cd Pruebas-de-software
python -m venv .venv
```

Activar el entorno virtual. En Windows con PowerShell:

```bash
.venv\Scripts\Activate.ps1
```

En Linux o macOS:

```bash
source .venv/bin/activate
```

Instalar las dependencias:

```bash
pip install -r requirements.txt
```

## Configuración

Copiar el archivo de ejemplo y completarlo. El archivo `.env` no se versiona y
no debe subirse nunca al repositorio.

```bash
cp .env.example .env
```

Si `SENTRY_DSN` queda vacío, la aplicación funciona igual y solo escribe el log
local. Con un DSN válido, además envía las excepciones no controladas a Sentry.

### Qué llega a Sentry y qué no

La distinción es deliberada y es la que hace que el panel sirva para algo:

- **Los errores previstos del negocio no se reportan.** Un RUT mal escrito, un
  código de equipo duplicado o una transición de estado no permitida son
  situaciones esperadas: se le muestran al usuario y quedan en el log local.
  Si se reportaran, el panel se llenaría de ruido y los defectos reales
  quedarían enterrados.
- **Los defectos inesperados sí se reportan.** Un archivo JSON corrupto, un
  error de programación o cualquier excepción que no sea del dominio se envía
  a Sentry con el actor y la operación que lo provocó.
- **Quien ve el error recibe una referencia.** La aplicación le muestra el
  identificador del evento, para que pueda citarlo al reportar el problema y
  se encuentre el evento exacto en el panel.
- **La suite de pruebas nunca envía eventos**, aunque tengas el DSN
  configurado. Lo verifica el caso CP-39.

## Datos de demostración

El repositorio ya trae datos cargados en `data/`. Para regenerarlos desde cero:

```bash
python scripts/cargar_demo.py --forzar
```

El escenario incluye 2 encargados, 4 solicitantes, 10 unidades de equipo en
cinco categorías y 7 solicitudes, una por cada estado relevante, de modo que se
puede probar un atraso o un período de gracia sin esperar días reales.

Credenciales de demostración, públicas a propósito y válidas solo para este
ejercicio:

| Rol | Correo | Contraseña |
| --- | --- | --- |
| Encargado | camila.rojas@lab.cl | labadmin2026 |
| Encargado | diego.fuentes@lab.cl | labadmin2026 |
| Solicitante al día | ana.perez@alumnos.cl | demo12345 |
| Solicitante al día | bruno.silva@alumnos.cl | demo12345 |
| Solicitante con atraso | diana.torres@alumnos.cl | demo12345 |

Diana Torres está en estado `pendiente` por un préstamo atrasado, así que sirve
para comprobar que el sistema le impide pedir equipos nuevos.

## Ejecución

```bash
python main.py
```

El archivo `main.py` de la raíz se encarga de la ruta de importación, así que
funciona igual en Windows, Linux y macOS sin configurar `PYTHONPATH`.

La aplicación pide correo y contraseña, y según el rol muestra el menú del
solicitante o el del encargado. Un correo vacío en la pantalla de ingreso cierra
la aplicación.

## Pruebas

```bash
python -m pytest
```

Para ejecutar solo una categoría de casos:

```bash
python -m pytest -m borde
```

Las categorías disponibles son `funcional`, `borde`, `negativo`, `reglas` y
`escenario`. Las pruebas corren contra un directorio temporal y nunca modifican
los datos de `data/`.

Los casos marcados como `xfail` corresponden a requerimientos todavía no
implementados: están escritos y sirven de contrato para quien los implemente.

## Estructura del proyecto

```
main.py              punto de entrada, resuelve la ruta de importación
Makefile             atajos para Linux y macOS
make.ps1             los mismos atajos para Windows
src/prestamos/
  almacen.py         lectura y escritura atómica de los JSON
  modelos.py         esquema de las cuatro entidades
  estados.py         máquina de estados de una solicitud
  disponibilidad.py  cálculo de qué equipos están libres
  validaciones.py    RUT, correo, fechas, rangos
  seguridad.py       hash de contraseñas
  registro.py        log de eventos e integración con Sentry
  servicios/         un módulo por área funcional
  cli/               menús de línea de comando
data/                archivos JSON de persistencia
docs/                reglas, estados, supuestos, trazabilidad y estrategia
evidencias/          salidas de ejecución de las pruebas, por fecha
scripts/             carga de datos de demostración
tests/               suite de pytest
```

## Documentación

- [Reglas de negocio, alcance y exclusiones](docs/reglas-de-negocio.md)
- [Estados y transiciones del préstamo](docs/estados-y-transiciones.md)
- [Supuestos y ambigüedades detectadas](docs/supuestos.md)
- [Matriz de trazabilidad](docs/matriz-trazabilidad.md)
- [Estrategia de pruebas](docs/estrategia-pruebas.md)
- [Flujo de trabajo con Git y reparto del equipo](docs/flujo-git.md)
- [Evidencia de la integración con Sentry](evidencias/sentry/README.md)

## Seguridad

Las contraseñas se guardan con PBKDF2-HMAC-SHA256 y sal aleatoria, nunca en
texto plano. El repositorio no contiene tokens ni secretos: el DSN de Sentry
vive en `.env`, que está en `.gitignore`.

## Autores

- [@xReNatS](https://github.com/xReNatS)
- [@gonzzza-lol](https://github.com/gonzzza-lol)

## Licencia

MIT. Ver el archivo [LICENSE](LICENSE).
