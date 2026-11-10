# Backend — API TecnoStock

API REST en FastAPI con acceso a SQL Server mediante `pyodbc`. No usa ORM:
todas las operaciones se ejecutan con `EXEC` sobre procedimientos almacenados.

## Arquitectura por capas

```
src/backend/
├── api/
│   ├── deps.py          # dependencias: usuario autenticado y servicios
│   └── routes/          # auth, categorias, productos, movimientos, dashboard
├── core/
│   ├── config.py        # Pydantic Settings (.env)
│   ├── database.py      # pool pyodbc (autocommit, transacciones en los SP)
│   ├── errors.py        # AppError, catálogo 500xx -> HTTP y manejadores
│   └── security.py      # Argon2id, JWT, dependencia Bearer
├── repositories/        # único punto de acceso a SQL (solo SP)
├── schemas/             # Pydantic: entrada con Decimal, salida con float
├── services/            # reglas de negocio y traducción de resultados
└── main.py              # app factory, CORS, lifespan y bootstrap del admin
```

- **APIs**: validan la petición, resuelven el usuario desde el JWT y devuelven
  los esquemas de salida.
- **Services**: aplican reglas (fechas del dashboard, armado de páginas, etc.)
  y no conocen SQL.
- **Repositories**: ejecutan los SP y traducen `pyodbc.Error` a `AppError`.
- **Schemas**: contrato público. Las entradas usan `Decimal` para dinero y las
  salidas `float` para que el JSON no contenga cadenas decimales.

## Configuración

Copiar `.env.example` a `.env` y completar:

| Variable | Descripción |
|---|---|
| `DB_SERVER` / `DB_NAME` | Instancia y base (por defecto `.\SQLEXPRESS` / `TecnoStock`). |
| `DB_TRUSTED_CONNECTION` | `true` usa autenticación de Windows (desarrollo). |
| `DB_USER` / `DB_PASSWORD` | Login SQL para producción con privilegio mínimo. |
| `DB_ENCRYPT`, `DB_TRUST_SERVER_CERTIFICATE` | Cifrado ODBC (Driver 18). |
| `DB_POOL_SIZE`, `DB_TIMEOUT` | Tamaño del pool y timeout de conexión. |
| `JWT_SECRET` | Secreto HS256 de al menos 32 caracteres. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Vigencia del token (120 por defecto). |
| `CORS_ORIGINS` | Orígenes permitidos, separados por coma. |
| `BOOTSTRAP_ADMIN_*` | Administrador inicial; solo se crea si no existe. |

El archivo `.env` está ignorado por Git. Nunca se versionan secretos.

## Ejecución

```powershell
uv sync
uv run backend
```

- El entry point `backend` ejecuta `backend.main:run()` y fija el event loop
  `SelectorEventLoop` en Windows (`backend.core.loop:event_loop_factory`).
  Es el modo recomendado: evita que un `WinError 64` cierre el socket de
  escucha cuando un cliente aborta la conexión.
- Si se arranca uvicorn directamente, hay que pasar la misma fábrica:

  ```powershell
  uv run uvicorn backend.main:app --reload --loop backend.core.loop:event_loop_factory --port 8000
  ```

- Documentación: <http://localhost:8000/docs>
- Salud: `GET /api/health` (verifica conexión a la base). También existe el
  alias `GET /health`, sin autenticación y con el mismo cuerpo, para sondas
  de disponibilidad.
- Login: `POST /api/auth/login` → `access_token` + usuario
- `GET /api/auth/me` → usuario autenticado

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/auth/login` | Inicio de sesión (Argon2id + JWT). |
| GET | `/api/auth/me` | Usuario del token. |
| GET/POST | `/api/categorias` | Listar / registrar. |
| GET/PUT | `/api/categorias/{id}` | Obtener / actualizar. |
| GET/POST | `/api/productos` | Listar con filtros / registrar (stock 0). |
| GET/PUT | `/api/productos/{id}` | Obtener / actualizar sin tocar stock. |
| PATCH | `/api/productos/{id}/activar` | Reactivar. |
| PATCH | `/api/productos/{id}/desactivar` | Desactivar (conserva stock e historial). |
| GET | `/api/productos/stock-bajo` | Activos con `Stock <= StockMinimo`. |
| GET | `/api/productos/valor-inventario` | `SUM(Stock * PrecioCompra)`. |
| POST | `/api/movimientos/entradas` | Entrada transaccional. |
| POST | `/api/movimientos/salidas` | Salida transaccional (sin stock negativo). |
| GET | `/api/movimientos` | Historial paginado y filtrable. |
| GET | `/api/dashboard` | KPIs, serie diaria y últimos movimientos. |

Todos los endpoints salvo login y salud requieren `Authorization: Bearer <JWT>`.

## Errores de negocio

| Código SQL | HTTP | `code` de la API |
|---:|---:|---|
| 50011 | 409 | `categoria_duplicada` |
| 50012 | 404 | `categoria_no_encontrada` |
| 50027 | 409 | `producto_duplicado` |
| 50028 | 404 | `producto_no_encontrado` |
| 50033 | 409 | `producto_no_disponible` (inactivo o inexistente) |
| 50034 | 409 | `stock_insuficiente` |
| 50035 | 422 | `categoria_no_encontrada` (al crear/editar producto) |

Las validaciones de Pydantic responden `422` con `code: "datos_invalidos"` y el
detalle por campo. Los repositorios traducen los errores de SQL antes de cruzar
el límite del endpoint (Starlette vuelve a lanzar excepciones no controladas).

## Pruebas

```powershell
uv run pytest
```

40 pruebas aprobadas: unitarias y de integración real contra la base `TecnoStock`.

Pruebas unitarias (no requieren base de datos):

- Event loop: la fábrica devuelve `SelectorEventLoop` en Windows y `run()` la
  pasa correctamente a uvicorn.

Pruebas de integración reales contra `TecnoStock`:

- Autenticación, token inválido, usuario inactivo y validaciones.
- Salud: `/api/health` y su alias `/health`.
- Categorías: alta, duplicados, actualización y 404.
- Productos: stock inicial 0, stock ignorado en alta/edición, filtros,
  activación/desactivación, stock bajo y valor de inventario.
- Movimientos: entrada/salida, stock insuficiente, historial, filtros y paginación.
- Dashboard: rango por defecto (mes actual), rango personalizado y KPIs.
- Concurrencia: 20 salidas simultáneas sobre stock 10 → 10 éxitos, 10 rechazos,
  stock final 0.

Los datos de prueba usan prefijos `TST-` / `TSTCAT-` y se eliminan antes y
después de la sesión. La limpieza directa con `pyodbc` es exclusiva de pruebas.

## Decisiones técnicas

- Pool `pyodbc` en `autocommit=True`: los SP abren y confirman su propia
  transacción, por lo que el driver no debe envolverlos en otra.
- Los errores `pyodbc.Error` se convierten a `AppError` en el repositorio; así
  el manejador HTTP devuelve 4xx aunque la excepción ocurra en un hilo.
- El administrador inicial se crea en el `lifespan` de la app porque el hash
  Argon2id solo puede generarse en Python. `06_seed.sql` solo inserta categorías.
- Los SP validan reglas de negocio y registran el movimiento dentro de la misma
  transacción que actualiza `Productos.Stock` (con `UPDLOCK`/`ROWLOCK`).
