# Base de datos TecnoStock

Scripts de SQL Server del sistema. Todo el acceso de la aplicación pasa por
procedimientos almacenados; no hay ORM ni DML directo desde el backend.

## Orden de ejecución obligatorio

Ejecutar con SSMS o `sqlcmd`, siempre en este orden. En Windows con
autenticación integrada y certificado autofirmado:

```powershell
sqlcmd -S ".\SQLEXPRESS" -E -C -f 65001 -b -i 01_database.sql -W -s "|"
```

| Orden | Script | Función |
|---:|---|---|
| 1 | `01_database.sql` | Crea la base `TecnoStock` si no existe y fija el nivel de compatibilidad (mínimo 110). |
| 2 | `02_tables.sql` | Crea `Usuarios`, `Categorias`, `Productos` y `MovimientosInventario`. |
| 3 | `03_constraints_indexes.sql` | Agrega PK, UNIQUE, FK, CHECK e índices (batch único con verificación previa). |
| 4 | `04_procedures.sql` | Crea o actualiza los 24 procedimientos almacenados. |
| 5 | `05_permissions.sql` | Crea el rol `TecnoStockApp` con privilegio mínimo. |
| 6 | `06_seed.sql` | Inserta 5 categorías iniciales de forma idempotente. |
| 7 | `07_verification.sql` | Verificación de solo lectura; imprime `RESULTADO GLOBAL: OK`. |

Los archivos están codificados en **UTF-8 con BOM** para que `sqlcmd` y SSMS
conserven los acentos. El parámetro `-f 65001` fuerza la página de códigos UTF-8.

## Idempotencia y protección contra ejecuciones fuera de orden

- `01` crea la base solo si no existe y fija la compatibilidad a
  `max(nivel_actual, 110)` para que `THROW` funcione siempre.
- `02` crea cada tabla solo si no existe (`IF OBJECT_ID(...) IS NULL`). No
  modifica tablas ya creadas. Cualquier cambio posterior debe ir en un script
  nuevo (`08_...sql` en adelante) con `ALTER TABLE` explícito.
- `03` es un **único batch** que verifica las columnas requeridas antes de
  aplicar DDL. Si falta una tabla aborta con el error `51000`; si falta una
  columna, con `51001`, y muestra un resultado de diagnóstico. Así un script
  ejecutado antes de tiempo produce **un solo error claro**, no una cascada.
- `04` y `05` usan `CREATE OR ALTER` y comprobaciones de existencia, por lo que
  pueden reejecutarse sin duplicar objetos.
- `06` solo inserta categorías que no existen por nombre.

Ningún script crea logins de SQL Server ni guarda credenciales. En desarrollo se
usa autenticación de Windows sobre `.\SQLEXPRESS`; para producción, crear un
login SQL y mapearlo al rol `TecnoStockApp` (ver `05_permissions.sql`).

## `04_procedures.sql` (24 procedimientos)

| Grupo | Procedimientos |
|---|---|
| Usuarios | `usp_Usuarios_ObtenerPorNombreUsuario`, `usp_Usuarios_ObtenerPorID`, `usp_Usuarios_Insertar`, `usp_Usuarios_Listar`, `usp_Usuarios_ActualizarClaveHash` |
| Categorías | `usp_Categorias_Listar`, `usp_Categorias_Obtener`, `usp_Categorias_Insertar`, `usp_Categorias_Actualizar` |
| Productos | `usp_Productos_Listar`, `usp_Productos_Obtener`, `usp_Productos_Insertar`, `usp_Productos_Actualizar`, `usp_Productos_Desactivar`, `usp_Productos_Activar`, `usp_Productos_StockBajo`, `usp_Productos_ValorInventario` |
| MovimientosInventario | `usp_MovimientosInventario_RegistrarEntrada`, `usp_MovimientosInventario_RegistrarSalida`, `usp_MovimientosInventario_Listar` |
| Dashboard | `usp_Dashboard_Resumen`, `usp_Dashboard_MovimientosPorDia`, `usp_Dashboard_TopProductos`, `usp_Dashboard_UltimosMovimientos` |

Reglas implementadas en los procedimientos:

- `Productos` se crea siempre con `Stock = 0`; el alta no recibe stock y la
  actualización no lo modifica.
- La actualización de producto asigna `FechaActualizacion = SYSDATETIME()`.
- Entradas y salidas se ejecutan en transacción, actualizan el stock con
  `UPDLOCK`/`ROWLOCK` y registran `StockAnterior` y `StockPosterior`.
- Una salida mayor al stock lanza `50034`; un producto inactivo o inexistente
  lanza `50033`; nunca se permite stock negativo.
- El historial es inmutable y conserva motivo, usuario, cantidades y fechas.
- Valor del inventario: `SUM(Stock * PrecioCompra)`, incluyendo productos
  inactivos con existencias.
- Stock bajo: solo productos activos con `Stock <= StockMinimo`.
- El identificador `MovimientosInventario` se usa sin variantes en tabla,
  procedimientos, repositorios, esquemas y API.

## `05_permissions.sql`

Crea el rol `TecnoStockApp` y aplica:

```sql
GRANT EXECUTE ON SCHEMA::dbo TO TecnoStockApp;
DENY SELECT, INSERT, UPDATE, DELETE ON SCHEMA::dbo TO TecnoStockApp;
```

La aplicación solo puede ejecutar procedimientos; cualquier DML directo es
rechazado. El login SQL y su contraseña se crean fuera de estos scripts.

## Administrador inicial

`06_seed.sql` **no** crea usuarios: las contraseñas se almacenan con Argon2id y
el hash debe generarse en Python. El backend crea el administrador inicial desde
`BOOTSTRAP_ADMIN_*` la primera vez que arranca, solo si el usuario no existe.

## `07_verification.sql`

Solo lectura: no crea, altera ni elimina objetos ni datos. Comprueba:

1. Existencia de las cuatro tablas y columnas por tabla.
2. Columnas, tipos, longitud, nulabilidad, `IDENTITY` y `DEFAULT`.
3. PK y `UNIQUE` con sus columnas en orden.
4. FK con tabla/columna referenciada y acciones `ON DELETE` / `ON UPDATE`.
5. CHECK con su definición y estado (`is_disabled`, `is_not_trusted`).
6. Índices con columnas clave, orden y `INCLUDE`.
7. Conteo de filas por tabla.
8. Integridad: stocks negativos, aritmética de movimientos, salidas mayores al
   stock y coherencia entre `Productos.Stock` y el último movimiento.
9. Existencia de los 24 procedimientos almacenados.
10. Rol `TecnoStockApp`, `EXECUTE` otorgado y los cuatro permisos denegados.

Al final imprime el detalle y `RESULTADO GLOBAL: OK` si todo es correcto.
