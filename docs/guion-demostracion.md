# Guion de demostración

Recorrido de cinco minutos por lo que el sistema ya hace, pensado para que
cualquiera lo reproduzca siguiendo solo estos pasos. Cada acto muestra una
decisión de diseño, no solo una pantalla.

Los números de opción corresponden al menú actual. El caso CP-44 falla si
alguien reordena las opciones, para avisar que este documento hay que
revisarlo: los números se corren en cuanto se agrega una opción intermedia.

## Antes de empezar

```powershell
.\make.ps1 reiniciar
.\make.ps1 correr
```

`reiniciar` deja los datos de demostración recién cargados, así que la
demostración parte siempre del mismo estado.

Credenciales:

| Rol | Correo | Contraseña |
| --- | --- | --- |
| Encargada | camila.rojas@lab.cl | labadmin2026 |
| Solicitante al día | ana.perez@alumnos.cl | demo12345 |
| Solicitante con atraso | diana.torres@alumnos.cl | demo12345 |

La contraseña no se ve al escribirla. Es intencional.

---

## Acto 1. La disponibilidad no se guarda, se calcula

**Entra como solicitante:** `ana.perez@alumnos.cl`

Opción **1**, Buscar equipos disponibles, y Enter en el texto de búsqueda.

> Ana ve **tres** equipos: LAP-002, LAP-003 y ARD-002.

Sal con **0** y Enter en el correo, luego entra como **encargada**.

Opción **7**, Ver catálogo de equipos, y Enter.

> Camila ve **diez**, cada uno con su estado: `disponible`, `en_uso` o
> `fuera_de_servicio`.

**Qué mostrar acá.** Abre `data/equipos.json` en otra ventana: LAP-001 dice
`"estado": "disponible"`. Pero el catálogo lo muestra `en_uso`. El estado no
se guarda duplicado, se deriva de las solicitudes activas, así que no puede
quedar desincronizado con la realidad.

Opción **8**, detalle, código `LAP-001`.

> Dice quién lo tiene tomado, con qué solicitud y hasta cuándo.

---

## Acto 2. Una solicitud sin aprobar ya bloquea el equipo

Sigue como encargada. Opción **8**, detalle, código `LAP-001` otra vez.

> El motivo nombra la solicitud **SOL-0001**, que está en estado
> `por_revisar`. Nadie la aprobó todavía y el equipo ya está bloqueado.

**Qué mostrar acá.** Fue una decisión del equipo frente a una ambigüedad del
enunciado, y está documentada en `docs/supuestos.md`, punto A05. Como un
préstamo puede extenderse una semana más, el sistema no puede prometer que una
unidad se desocupe en una fecha futura. Bloquear desde el primer momento
resuelve además la carrera entre dos personas que piden lo mismo: gana quien
registra primero.

---

## Acto 3. Las reglas se defienden solas

Sigue como encargada.

**Un RUT inventado no entra.** Opción **1**, Registrar solicitante. Nombre
`Prueba Falsa`, RUT `12345678-9`, correo `prueba@alumnos.cl`, contraseña
`clave12345`.

La aplicación pide los cuatro datos antes de validar nada, así que hay que
completarlos todos aunque el RUT ya sea inválido.

> `[error] RUT invalido: digito verificador incorrecto`

Es el mismo cuerpo que el RUT de Ana Pérez con el dígito cambiado, así que
demuestra que la validación calcula de verdad y no solo mide el largo.

**Un correo no puede tener dos roles.** Opción **1** otra vez. Nombre
`Impostora`, RUT `15000000-9`, correo `camila.rojas@lab.cl`, contraseña
`clave12345`.

> `[error] El correo camila.rojas@lab.cl ya esta registrado como encargado`

Si se permitiera, el rol de la sesión dependería del orden en que el login
busca en cada archivo.

**Un código de equipo no se repite.** Opción **5**, Registrar equipo, código
`lap-001`, nombre `Otro notebook`, categoría `laptop`, y Enter en la
descripción, que es opcional.

> `[error] Ya existe un equipo con el codigo LAP-001`

En minúsculas, para mostrar que el código se normaliza antes de comparar.

**No se retira un equipo que alguien tiene.** Opción **6**, código `PRO-001`,
acción `retirar`, motivo `Revision tecnica`.

> `[error] El equipo PRO-001 esta tomado por la solicitud SOL-0003 ...
> Cierre o cancele esa solicitud antes de retirar el equipo.`

Sin esta regla, la solicitud quedaría apuntando a un equipo que el sistema
considera inexistente.

---

## Acto 4. Registrar de verdad, y ver el efecto

Opción **5**, Registrar equipo. Código `MIC-001`, nombre `Microscopio USB`,
categoría `microscopio`, descripción `Aumento 1000x`.

Opción **7**, catálogo, buscar `micro`.

> Aparece, y como `disponible`.

Opción **1**, Registrar solicitante. Nombre `Elena Diaz`, RUT `15000000-9`,
correo `elena.diaz@alumnos.cl`, contraseña `clave12345`.

Opción **3**, Ver personas autorizadas.

> Elena aparece en la tabla, en estado `al_dia`. Ninguna fila muestra el hash
> de la contraseña.

**Qué mostrar acá.** En otra ventana:

```powershell
Select-String -Path data\*.json -Pattern "clave12345"
```

> No devuelve nada. Las contraseñas se guardan con PBKDF2 y sal aleatoria.

---

## Acto 5. El atraso bloquea, y lo decide el sistema

Opción **3**, Ver personas autorizadas.

> Diana Torres aparece en estado `pendiente`, mientras el resto está `al_dia`.

Ese estado no lo puso una persona: lo calculó el sistema cuando venció el
período de gracia de su préstamo, que es la solicitud SOL-0005, hoy en estado
`atrasada`. Un solicitante en `pendiente` no puede pedir equipos nuevos.

---

## Acto 6. Todo queda registrado

Opción **15**, Ver log de eventos.

> Aparecen los ingresos, los registros de Elena y del microscopio, y los
> intentos fallidos. Cada línea trae la hora, el tipo de evento y quién lo
> hizo.

**Qué mostrar acá.** El log distingue lo previsto de lo inesperado. Los errores
de este guion, un RUT malo o un código repetido, quedan en el log local y **no**
se reportan a Sentry: son situaciones esperadas del negocio. A Sentry solo
llegan los defectos, con la traza, las variables y el commit exacto. La
evidencia de eso está en `evidencias/sentry/`.

---

## Acto 7. El ciclo completo del préstamo

Ya no queda ninguna opción pendiente: los once requerimientos funcionan. Para
recorrer un préstamo entero hacen falta las dos cuentas, alternando.

| Quién | Opción | Datos |
| --- | --- | --- |
| Ana | `3` Crear solicitud | Código `LAP-002`, retiro hoy, devolución en tres días |
| Ana | `4` Ver mis solicitudes | Aparece en `por_revisar` |
| Camila | `10` Aprobar | El id que salió, por ejemplo `SOL-0009` |
| Camila | `13` Registrar entrega | El mismo id. Pasa a `en_prestamo` |
| Ana | `6` Declarar devolución | El mismo id |
| Camila | `14` Confirmar devolución | El mismo id, observación `Sin daños` |
| Camila | `7` Ver catálogo | `LAP-002` volvió a estar `disponible` |

**Qué mostrar acá.** Declarar la devolución **no** libera el equipo. Entre el
paso de Ana y el de Camila, el catálogo sigue mostrando `LAP-002` en uso. La
unidad se libera solo cuando el encargado confirma que la recibió, porque la
responsabilidad física es de quien tiene el equipo en la mano. Esa fue una
decisión del equipo frente a una ambigüedad del enunciado, documentada en
`docs/supuestos.md`, punto A07.

---

## Cierre: las pruebas

```powershell
.\make.ps1 verificar
```

Muestra la suite completa y el recuento de casos por categoría frente al
mínimo que exige la tarea.
