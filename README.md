# Motor Contable — Prueba Técnica

Módulo contable que permite administrar un plan de cuentas, registrar comprobantes (con partida doble), consultar el libro mayor, y generar el archivo de información exógena. Incluye login con JWT y se levanta completo con Docker Compose.

## Demo en vivo

**http://161.97.86.251:3001** — usuario `admin`, contraseña `admin123`.

Es una instancia real corriendo con Docker Compose en un VPS (no un mock ni capturas de pantalla), con datos de demostración ya cargados (empresa, plan de cuentas, terceros y un comprobante contabilizado) para poder probar todo — incluida la generación de exógena — sin tener que crear nada a mano primero. Es un servidor de prueba para esta entrega, no un servicio con garantía de disponibilidad continua.

## Cómo explicar este proyecto en 2 minutos

Es un backend en **FastAPI** con una base de datos **PostgreSQL**, y un frontend en **Next.js** que lo consume. La idea central es la contabilidad de partida doble: cada comprobante tiene líneas con débito o crédito, y antes de "contabilizarlo" (dejarlo en firme) el sistema valida que cuadre, que las cuentas existan y estén activas, y que el período no esté cerrado. Una vez contabilizado, un comprobante **no se puede editar ni borrar** — si hay un error, se "revierte" (se crea un comprobante inverso nuevo), para no perder el rastro de lo que pasó.

El resto de las piezas giran alrededor de esa idea:
- **Plan de cuentas**: el catálogo de cuentas contra las que se contabiliza.
- **Libro mayor**: la consulta de movimientos de una cuenta, con saldo acumulado.
- **Exógena**: un reporte XML anual agrupado por tercero, con un umbral en UVT para decidir qué terceros se incluyen.
- **Login (JWT)**: toda la API exige estar autenticado, excepto el login mismo.

## Stack

| Capa | Tecnología |
|---|---|
| Backend | FastAPI + SQLAlchemy + PostgreSQL |
| Frontend | Next.js (App Router) + TypeScript |
| Autenticación | JWT propio (sin proveedor externo) |
| Contenedores | Docker Compose |
| Pruebas | pytest, contra una base PostgreSQL real |

## Cómo está organizado el código

El backend está separado en capas, cada una con una sola responsabilidad:

```
motor-contable-backend/app/
  api/        endpoints de FastAPI (reciben el request, llaman al service, devuelven la respuesta)
  services/   la lógica de negocio real (reglas de contabilización, exógena, etc.)
  models/     tablas de la base de datos (SQLAlchemy)
  schemas/    validación de entrada/salida (Pydantic)
  core/       configuración, conexión a BD, seguridad (JWT)
```

La idea es que un endpoint en `api/` nunca decide reglas de negocio por su cuenta: solo recibe el request, se lo pasa a una función de `services/`, y esa función es la que sabe *de verdad* cómo funciona la contabilidad. Esto facilita probar las reglas de negocio sin tener que levantar un servidor HTTP (ver la sección de pruebas).

El frontend sigue un patrón parecido: cada `services/*.ts` es el único lugar que le habla al backend (usando `apiClient.ts`, que agrega el token de sesión automáticamente); los componentes de `app/` y `components/` solo llaman a esos services.

## 1. Levantar el proyecto en local

### Opción A — Docker Compose (recomendada, un solo comando)

Requisitos: tener Docker Desktop instalado y corriendo.

```bash
docker compose up --build
```

Esto levanta tres contenedores:
- `db`: PostgreSQL 16, con un volumen para que los datos persistan entre reinicios.
- `backend`: FastAPI en `http://localhost:8000`.
- `frontend`: Next.js en `http://localhost:3000`.

El backend crea las tablas solo (ver "Migraciones" abajo) y siembra datos de demostración automáticamente, para no tener que crear nada a mano antes de poder probar:

- Un usuario: `admin` / `admin123`.
- Una empresa ("Empresa Demo SAS"), su plan de cuentas básico y un período abierto.
- Dos terceros (un proveedor y un cliente).
- Un comprobante ya contabilizado con un tercero, por un valor que supera el umbral típico de exógena (42 UVT) — así la exógena tiene algo real que reportar desde el primer intento.

Todo esto es idempotente: si reinicias el contenedor no se duplica (se siembra una sola vez, buscando por NIT). Con eso ya puedes entrar a `http://localhost:3000` y usar la app de punta a punta, incluida la generación de exógena.

### Opción B — Manual (backend y frontend por separado)

**Backend** (necesitas PostgreSQL corriendo en tu máquina):

```powershell
cd motor-contable-backend
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Configura la variable `DATABASE_URL` si tu Postgres no usa las credenciales por defecto (ver `app/core/config.py`), y luego:

```powershell
uvicorn app.main:app --reload
```

**Frontend** (en otra terminal):

```powershell
cd frontend-contable
npm install
npm run dev
```

El frontend espera el backend en `http://127.0.0.1:8000/api` (configurable en `frontend-contable/.env`).

## 2. Migraciones

**No hay migraciones formales con Alembic todavía** (aunque la librería está en `requirements.txt`, quedó sin inicializar). Las tablas se crean automáticamente al arrancar el backend, con `Base.metadata.create_all()` en `app/main.py` — esto crea cualquier tabla que falte, pero **no modifica una tabla que ya existe** si le agregas una columna nueva al modelo.

En la práctica esto solo importa si ya tenías una base de datos de una versión anterior del proyecto; en una base nueva (como la que crea Docker Compose la primera vez) no hay ningún paso adicional que correr. Más detalle de esta limitación y cómo la resolvería en la sección de "Pendientes".

## 3. Cómo correr las pruebas

Las pruebas corren contra una base de datos PostgreSQL real (no un mock ni SQLite), porque varias reglas dependen de comportamiento real de Postgres — en particular, el bloqueo de filas (`SELECT ... FOR UPDATE`) que evita números de comprobante duplicados si dos personas contabilizan al mismo tiempo.

```powershell
cd motor-contable-backend
venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
pytest -v
```

Se conecta a `motor_contable_test` (se crea sola si no existe, usando las mismas credenciales que tu Postgres local). Cada prueba corre dentro de una transacción que se revierte al final, así que no ensucia la base entre pruebas ni necesita recrear el esquema cada vez.

**67 pruebas**, organizadas por lo que protegen:

| Archivo | Qué prueba |
|---|---|
| `test_comprobante_schema.py` | Partida doble, mínimo dos líneas, valores negativos, decimales excesivos |
| `test_comprobante_service.py` | Consecutivo, cuentas inactivas, período cerrado, precisión monetaria |
| `test_reversion_service.py` | Reversión: contraasiento balanceado, no revertir dos veces |
| `test_borrador_service.py` / `test_borrador_api.py` | Guardar/editar borrador, contabilizar un borrador |
| `test_periodos_api.py` | Cierre de período (incluye la regresión de un bug real que se corrigió) |
| `test_exogena_service.py` | Dígito de verificación del NIT, agrupación, umbral en UVT |
| `test_reportes_api.py` | Libro mayor: precisión decimal, nombre del tercero |
| `test_concurrencia.py` | Dos contabilizaciones simultáneas no duplican consecutivo |
| `test_auth_api.py` / `test_auditoria_usuario.py` | Login, rutas protegidas, quién hizo cada operación |

No hay pruebas automatizadas de frontend — con el tiempo disponible prioricé proteger las reglas de negocio del backend, que es donde vive el riesgo real (dinero, partida doble, concurrencia).

## 4. Flujo funcional (cómo se usa)

1. **Login** con `admin` / `admin123` (o el usuario que crees).
2. **Plan de cuentas**: revisar o crear las cuentas contra las que se va a contabilizar.
3. **Nuevo comprobante**: agregar empresa, fecha, descripción y líneas (cuenta, tercero opcional, débito o crédito). Se puede:
   - **Guardar borrador**: queda guardado tal cual esté, aunque no cuadre o le falten líneas.
   - **Contabilizar**: aquí sí se exige que cuadre, que tenga mínimo dos líneas, cuentas activas y período abierto. Si venías de un borrador, lo promueve; si no, lo crea y contabiliza de una vez.
4. **Libro mayor**: elegir una cuenta y un rango de fechas para ver sus movimientos y el saldo acumulado.
5. **Cierre de período**: bloquea que se sigan contabilizando comprobantes en ese mes (los que ya quedaron en borrador sin terminar sí bloquean el cierre).
6. **Reversión**: si un comprobante contabilizado tenía un error, se revierte — se genera un comprobante inverso nuevo, y el original queda marcado como revertido pero nunca se borra ni se edita.
7. **Exógena**: elegir empresa, año gravable y umbral en UVT, y descargar el XML. El historial de generaciones se puede re-descargar después.

## 5. Decisiones de diseño

**Plan de cuentas simple.** El código de cuenta es la llave primaria (no un UUID aparte), y `parent_codigo` es una referencia opcional a otra cuenta para permitir una jerarquía simple (una cuenta "padre" con varias "hijas"). No modelé niveles, tipos de cuenta NIIF ni nada más elaborado — para el alcance de esta prueba, más estructura no agregaba valor y sí complejidad.

**Borrador con validación relajada, contabilizar con validación estricta.** Un borrador puede quedar incompleto o desbalanceado a propósito (es un work-in-progress); todas las reglas de partida doble, mínimo de líneas, cuentas activas y período abierto se aplican solo al contabilizar. Un borrador tampoco consume número de comprobante — el consecutivo se asigna solo cuando algo queda en firme.

**Reversión con contraasiento, no edición ni borrado.** Elegí generar un comprobante inverso nuevo en vez de "deshacer" el original, porque así el libro mayor siempre refleja exactamente lo que pasó — nunca desaparece un movimiento que ya se contabilizó, lo cual es importante para trazabilidad y para cualquier auditoría.

**Libro mayor calculado en tiempo real, no con saldos acumulados guardados.** Cada consulta recalcula el saldo recorriendo los movimientos de la cuenta ordenados por fecha. Es más simple y siempre está actualizado (no hay riesgo de que un saldo "cacheado" quede desincronizado), a costa de que una cuenta con muchísimo historial tarde más en consultarse. Para el volumen de una empresa normal esto no es un problema real; si llegara a serlo, la alternativa sería mantener un saldo acumulado por cuenta que se actualiza en cada contabilización, aceptando la complejidad extra de mantenerlo sincronizado.

**Precisión monetaria: `Decimal` en todas las capas, nunca `float`.** La base de datos usa `Numeric(20,2)`, los schemas de Pydantic usan `Decimal` con `decimal_places=2`, y — esto es un detalle no obvio — FastAPI serializa `Decimal` como **string** en el JSON (`"190000.00"`, no `190000.00`), precisamente para que el valor nunca pase por un `float` de JavaScript antes de que tú decidas convertirlo. El frontend respeta eso: los montos llegan como string y se convierten a número solo en el último momento, para mostrarlos.

**Concurrencia: bloqueo de fila sobre el período.** Antes de calcular el siguiente consecutivo, se hace `SELECT ... FOR UPDATE` sobre el período contable. Si dos comprobantes intentan contabilizarse al mismo tiempo en el mismo período, Postgres obliga al segundo a esperar a que el primero termine, así que nunca se generan dos comprobantes con el mismo número. Está probado con un test que lanza dos hilos reales contra la base de datos (`test_concurrencia.py`).

**Login con JWT y hash propio (PBKDF2), sin librerías externas de hashing.** Usé `hashlib.pbkdf2_hmac` con sal aleatoria en vez de `bcrypt`/`passlib`, para no sumar una dependencia binaria extra en un login que solo necesitaba ser razonablemente simple y seguro, no de nivel empresarial.

**Docker: el frontend corre en modo desarrollo (`next dev`), no un build de producción.** La variable `NEXT_PUBLIC_API_URL` la usa el *navegador*, no el contenedor, así que de todas formas tiene que apuntar a `localhost:8000` y no a un nombre interno de Docker. Usar modo desarrollo evita la complejidad de pasar esa variable como build-arg para una imagen de producción, y es más apropiado para que un evaluador pueda levantar el proyecto y curiosear el código con hot-reload.

**Extensión opcional elegida: Docker Compose + JWT.** De las opciones sugeridas, elegí estas dos porque juntas demuestran algo que valoro: que el proyecto no solo "funciona en mi máquina", sino que cualquiera lo puede levantar con un comando y que la API no queda abierta sin control de acceso. Verifiqué ambas de punta a punta con contenedores reales, no solo revisando el código.

## 6. Reapertura de período (no implementada)

Cerrar un período es sencillo (`POST /api/periodos/cerrar`), pero reabrirlo no está implementado. La estrategia que seguiría en una siguiente iteración:

1. **Control de acceso**: reabrir un período es una operación crítica, la protegería con un rol específico (ej. `ADMINISTRADOR_FINANCIERO`), no cualquier usuario autenticado.
2. **Trazabilidad obligatoria**: nunca cambiar `cerrado = false` en silencio. Exigiría un motivo en el request, y lo guardaría en una tabla de auditoría (`quién`, `cuándo`, `qué período`, `por qué`).
3. **Períodos posteriores**: si Febrero ya está cerrado y reabres Enero, cualquier ajuste en Enero podría afectar el saldo inicial de Febrero. La forma más simple de manejarlo es exigir que los períodos se reabran en orden inverso (el más reciente primero); una alternativa más elaborada sería recalcular en segundo plano los saldos de los períodos posteriores tras el ajuste.

## 7. Limitaciones conocidas

- **Sin Alembic**: las tablas se crean con `create_all()`, no hay historial de migraciones versionado. Ver sección de pendientes.
- **`consecutivo` sin constraint único en la base de datos**: la unicidad depende del bloqueo de fila (`SELECT FOR UPDATE`) en la aplicación, probado y funcionando, pero sin una red de seguridad a nivel de esquema si esa lógica cambiara por error.
- **El código de cuenta (`plan_cuentas.codigo`) es único globalmente, no por empresa.** Aunque cada cuenta tiene una columna `empresa_id`, la llave primaria es solo el código — dos empresas no podrían tener ambas una cuenta `"1105"` en la base actual. No es solo teórico: me topé con esto de frente al escribir el seed de datos de demostración (`app/core/seed.py`), que por eso usa códigos con prefijo `DEMO-` en vez de códigos contables "normales" — para no arriesgarme a chocar con cuentas que crees después para tu propia empresa. Para el alcance de esta prueba (probablemente una sola empresa a la vez) no genera problemas, pero es una limitación real para un caso multiempresa serio.
- **Sin gestión visual de terceros**: se pueden crear por API (`POST /api/terceros`) y elegir en el selector del comprobante, pero no hay una pantalla en el frontend para crear uno nuevo directamente.
- **Sin pruebas automatizadas de frontend.**
- **El estado `ANULADO` de un comprobante está contemplado en el modelo pero ningún flujo lo asigna todavía** — quedó reservado para una eventual funcionalidad de anulación distinta a la reversión.

## 8. Pendientes

- **Inicializar Alembic** y generar la migración inicial a partir del esquema actual, para dejar de depender de `create_all()` y de scripts sueltos (`add_dv_column.py`, etc.) cada vez que cambia un modelo.
- **Constraint único compuesto** (`empresa_id`, `periodo_id`, `consecutivo`) a nivel de base de datos, como respaldo del bloqueo aplicativo.
- **Pantalla de gestión de terceros** en el frontend.
- **CI básico** (GitHub Actions corriendo `pytest` y `tsc --noEmit` en cada push) — no lo prioricé porque ya había elegido Docker Compose y JWT como las dos mejoras de la sección opcional, pero sería el siguiente candidato natural.
- **Reapertura de período**, con la estrategia descrita arriba.

## 9. ¿Qué cambiaría para llevar esto a producción?

- **Alembic** en vez de `create_all()`, sin excepción — es el cambio no-negociable antes de tener usuarios reales.
- **Secrets reales**: `JWT_SECRET_KEY` sale de una variable de entorno hoy, pero el valor por defecto en `docker-compose.yml` es de desarrollo; en producción vendría de un gestor de secretos, no de un archivo versionado.
- **Refresh tokens** o expiración más corta del JWT (hoy son 8 horas fijas) con posibilidad de revocar sesiones.
- **Rate limiting** en `/api/auth/login` para evitar fuerza bruta sobre contraseñas.
- **Build de producción real del frontend** (`next build` + `next start`) en vez de `next dev` dentro del contenedor.
- **Logs y métricas estructuradas** (hoy son prints sueltos en un par de endpoints de exógena, quedaron de una fase de debugging y deberían limpiarse).
- **Backups y monitoreo de la base de datos**, y un plan de rollback para las migraciones.
