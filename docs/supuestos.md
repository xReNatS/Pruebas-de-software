# Supuestos y ambigüedades detectadas

El enunciado pedía una solución "simple, confiable, que evite problemas con los
préstamos" sin más detalle. Aquí queda registrada cada ambigüedad detectada, la
decisión que tomó el equipo y por qué. Toda decisión de esta lista está
reflejada en el código y en al menos un caso de prueba.

## A01. Datos obligatorios de cada entidad

El enunciado no define qué campos tiene una persona, un equipo ni una solicitud.

**Supuesto:** solicitante con nombre, RUT, correo, contraseña y estado. Encargado
con id, nombre, correo y contraseña. Equipo con código, nombre, categoría,
estado y descripción. Solicitud con id, RUT del solicitante, códigos de equipo,
fecha de retiro, fecha de devolución, estado e historial.

**Riesgo que queda:** no se guarda carrera ni departamento, así que no se podrán
hacer reportes por unidad académica.

## A02. Unidad física contra modelo de equipo

Si un equipo es un modelo y no una unidad, la disponibilidad se calcula con
conteos y no con bloqueos.

**Supuesto:** cada registro de equipo es una unidad física con código propio.
Varias unidades del mismo modelo comparten nombre y categoría. Esto es lo que
hace que la disponibilidad sea una pregunta binaria por unidad.

## A03. Duración del período de gracia

El material de la fase 1 dice "1 día" en las reglas de negocio y "dos días de
gracia" en la lista de ambigüedades. Es una contradicción interna.

**Decisión:** 1 día, tomado de la sección de reglas de negocio por ser la más
formal de las dos. Está en `reglas.DIAS_PERIODO_GRACIA`, de modo que cambiarlo
es modificar una constante y volver a ejecutar la suite.

## A04. Un encargado, ¿puede además pedir equipos?

**Decisión:** no. Las cuentas son separadas y un mismo correo no puede existir en
las dos colecciones. Simplifica los permisos y permite pruebas negativas claras
del tipo "un encargado intenta crear una solicitud".

**Riesgo que queda:** si un ayudante necesita pedir un equipo, alguien debe
crearle una segunda cuenta de solicitante con otro correo.

## A05. ¿"Aprobada" y "en préstamo" ocupan igual el equipo?

**Decisión:** sí, y además "por revisar" también ocupa. Un equipo queda
bloqueado desde que alguien lo pide y hasta que la solicitud se cierra. La razón
es que un préstamo puede extenderse una semana más, así que prometer una fecha
de liberación sería una promesa que el sistema no puede cumplir.

**Riesgo que queda:** baja la utilización del laboratorio. Una unidad pedida y
no aprobada queda inmovilizada.

## A06. Dos personas piden la misma unidad a la vez

**Decisión:** gana quien registre primero. Como la solicitud bloquea desde el
estado `por_revisar`, la segunda persona recibe un error que nombra la solicitud
que tiene tomada la unidad.

**Riesgo que queda:** la aplicación es de un solo proceso y no hay bloqueo de
archivos. Dos instancias corriendo al mismo tiempo sobre el mismo directorio de
datos podrían pisarse. Está declarado como riesgo abierto, no resuelto.

## A07. Los dos lados de la devolución (RF08 y RF10)

El enunciado define dos requerimientos distintos para lo que físicamente es un
solo hecho.

**Decisión:** RF10 es la declaración del solicitante y solo escribe la marca
`devolucion_declarada_en`. RF08 es la confirmación del encargado y es la única
que mueve la solicitud a `concluida` y libera la unidad. Así la máquina de
estados no necesita un estado intermedio y la responsabilidad física queda en
quien recibe el equipo.

## A08. ¿Se puede modificar una solicitud ya aprobada?

**Decisión:** no se edita. Se cancela y se crea otra. Toda cancelación exige un
motivo que queda en el historial de la solicitud.

## A09. ¿Qué significa "confiable" para el encargado?

Se tradujo a tres propiedades verificables: ninguna operación puede dejar el
archivo JSON a medio escribir, ninguna transición de estado puede ocurrir fuera
de la tabla de transiciones, y todo evento relevante queda en el log con su
actor y su marca de tiempo.

## A10. Anticipación máxima de una reserva

El enunciado no la fija.

**Supuesto:** no hay límite de anticipación, porque el bloqueo es inmediato de
todas formas. Lo que sí se limita es la duración, con un máximo de 7 días.

## A11. Estudiantes y profesores

**Supuesto:** mismos límites de cantidad y de tiempo para ambos. El modelo no
distingue subtipos de solicitante.

## A12. Estado del equipo escrito a mano

El campo `estado` del equipo podría desincronizarse de las solicitudes.

**Decisión:** el único valor manual es `fuera_de_servicio`. Los valores
`disponible` y `en_uso` se calculan leyendo las solicitudes activas.
