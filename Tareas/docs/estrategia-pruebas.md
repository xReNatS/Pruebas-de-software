# Estrategia de pruebas

## Objetivo

Comprobar que el sistema respeta las reglas de negocio de `reglas-de-negocio.md`
y la máquina de estados de `estados-y-transiciones.md`, y que ninguna entrada
inválida deja los archivos JSON en un estado inconsistente.

## Alcance

Entra: la capa de servicios, la máquina de estados, el cálculo de
disponibilidad, las validaciones de entrada y la persistencia.

No entra: la interacción por teclado de los menús, que se verifica de forma
manual con el guion de ejecución, y la integración real con Sentry, que se
comprueba una vez de forma manual provocando un error.

## Responsabilidades

Las pruebas están cruzadas. El integrante A diseña y ejecuta los casos que
verifican el código del integrante B, y viceversa, según el reparto de
`flujo-git.md`. Quien encuentra un defecto lo registra como Issue con la
plantilla de defecto; quien implementó el código lo corrige y la reejecución la
hace quien lo reportó.

## Ambiente

- Python 3.11 o superior, pytest 8.
- Cada prueba corre contra un directorio de datos temporal creado por la fixture
  `entorno_aislado`. Ninguna prueba lee ni escribe `data/`, así que la suite se
  puede ejecutar en cualquier orden y no ensucia los datos de demostración.
- Sentry queda desactivado durante las pruebas fijando `SENTRY_DSN` vacío.

## Datos de prueba

La fixture `datos_base` construye un escenario mínimo: un encargado, dos
solicitantes y tres equipos de categorías distintas. Los escenarios que
requieren tiempo transcurrido se montan con `crear_solicitud_directa`, que
inserta una solicitud ya en el estado deseado. Así no hay que esperar días
reales ni depender de código todavía no implementado.

## Criterios de entrada

- El requerimiento tiene su criterio de aceptación escrito en la matriz.
- El código está en una rama y la suite completa corre sin errores de importación.

## Criterios de salida

- Todos los casos asociados al requerimiento pasan.
- Ningún caso queda marcado `xfail` para un requerimiento que se declara terminado.
- Los defectos de severidad alta están cerrados y reejecutados.

## Registro de evidencias

La planilla de casos de prueba **se genera, no se escribe a mano**:

```bash
make planilla          # Linux o macOS
.\make.ps1 planilla    # Windows
```

Produce `evidencias/planilla-casos-de-prueba.csv`, listo para pegar en la
planilla del Aula, y `docs/casos-de-prueba.md` con la misma tabla en formato
legible. El resultado obtenido y el estado de cada caso salen de ejecutar la
suite de verdad, no de lo que alguien recuerde: la tarea considera incompleto
un caso que solo tenga el resultado esperado, y escribir a mano el obtenido es
la forma más fácil de que la planilla y el código dejen de coincidir.

El generador distingue tres situaciones que no son lo mismo:

- **Aprobado**, el caso pasa.
- **Defecto abierto**, el caso falla por un defecto ya registrado como Issue, y
  la planilla cita el número.
- **Pendiente de implementar**, el caso espera a que exista su requerimiento.

Además, la salida de la ejecución se guarda como archivo de texto por fecha:

```bash
python -m pytest -v > evidencias/pytest-AAAA-MM-DD.txt
```

Para el informe se adjunta además el resumen por categoría:

```bash
python -m pytest -m "funcional or borde or negativo or reglas or escenario" -q
```

El log de eventos de la aplicación, en `logs/eventos.log`, es la evidencia de
las pruebas manuales de los menús: cada operación relevante queda con su
actor y su marca de tiempo.

## Plantilla de caso de prueba

| Campo | Contenido |
| --- | --- |
| ID | CP-nn |
| Requerimiento | RFnn |
| Categoría | funcional, borde, negativo, reglas o escenario |
| Precondición | Estado de los datos antes de ejecutar |
| Pasos | Qué se ejecuta |
| Resultado esperado | Qué debería ocurrir |
| Resultado obtenido | Qué ocurrió realmente |
| Estado | Aprobado o fallido |
| Evidencia | Nombre de la prueba automatizada o archivo de salida |

## Plantilla de defecto

Al registrar un Issue de defecto se incluyen los pasos para reproducir, el
resultado esperado y el obtenido, la severidad con su justificación, la
evidencia, la referencia al commit que corrige y el resultado de la reejecución.
