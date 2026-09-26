# Flujo de trabajo con Git y reparto del equipo

## Flujo elegido: trunk-based con ramas cortas

`main` es la única rama de larga vida y siempre debe quedar en verde: la suite
de pruebas pasa en todo commit de `main`. Todo lo demás son ramas de vida corta
que nacen de `main`, viven uno o dos días y vuelven por pull request.

**Por qué este flujo y no GitFlow.** GitFlow separa `develop`, `release` y
`hotfix` para coordinar varias versiones publicadas al mismo tiempo. Este
proyecto tiene dos personas, una entrega y ninguna versión en producción, así
que esas ramas serían ceremonia sin beneficio. Trunk-based mantiene la
integración diaria, que es lo que de verdad reduce el riesgo de conflictos
grandes al final del plazo.

## Convención de ramas

```
feat/RF05-crear-solicitud
test/RF05-casos-borde
fix/RF07-aprobacion-sin-disponibilidad
docs/matriz-trazabilidad
```

El identificador del requerimiento va siempre en el nombre. Eso conecta la rama
con el Issue, con el caso de prueba y con la fila de la matriz de trazabilidad.

## Convención de commits

```
RF05: valida que la solicitud tenga uno o dos equipos

Implementa RN03 en crear_solicitud y agrega el caso CP-27.
Refs #12
```

La primera línea nombra el requerimiento y lo que cambió. El cuerpo explica por
qué. Se referencia el Issue con `Refs #n`, o con `Closes #n` cuando el pull
request cierra el trabajo.

## Regla de revisión

Ningún pull request se fusiona sin la aprobación de la otra persona. La revisión
no es un trámite: al menos un cambio del proyecto debe originarse en un
comentario de revisión, porque la tarea pide evidencia de eso.

## Reparto del trabajo

El reparto es por dominio funcional, no por capa, para que cada persona sea
dueña de archivos distintos y los conflictos de merge sean raros.

| Integrante | Implementa | Diseña y ejecuta pruebas de |
| --- | --- | --- |
| A | RF01 a RF04: autenticación, personas y equipos | RF05 a RF11 |
| B | RF05 a RF11: solicitudes, préstamos y devoluciones | RF01 a RF04 |

Las pruebas están cruzadas a propósito: cada integrante escribe los casos que
verifican el código de la otra persona. Los archivos
`tests/test_rf02_rf03_rf04_personas_equipos.py` y
`tests/test_rf05_a_rf11_solicitudes.py` ya contienen los esqueletos cruzados
marcados con `xfail`. Al implementar un requerimiento se quita la marca `xfail`
del caso correspondiente y el caso debe pasar sin que se toque su cuerpo. Si
para hacerlo pasar hay que cambiar la prueba, eso es una conversación entre los
dos, no un cambio silencioso.

## Base ya construida y compartida

Nadie debería necesitar reescribir estos módulos. Si alguno queda corto,
conviene avisarlo antes de modificarlo, porque los usan ambos lados.

| Módulo | Qué entrega |
| --- | --- |
| `almacen.py` | Lectura y escritura atómica de los JSON, búsquedas, ids correlativos |
| `modelos.py` | Fábricas de las cuatro entidades con su esquema y validaciones |
| `estados.py` | Tabla de transiciones y control de rol autorizado |
| `disponibilidad.py` | Cálculo de bloqueos y motivo legible de no disponibilidad |
| `validaciones.py` | RUT con dígito verificador, correo, fechas, rangos |
| `seguridad.py` | Hash y verificación de contraseñas |
| `registro.py` | Log de eventos y envío de excepciones a Sentry |
| `sesion.py` | Sesión y comprobación de rol |
| `cli/comun.py` | Menús, tablas y traducción de errores a mensajes |
| `tests/conftest.py` | Directorio de datos temporal y fixtures de sesión |
