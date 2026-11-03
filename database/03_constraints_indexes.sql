/*
    TecnoStock - 03_constraints_indexes.sql
    Agrega claves primarias, claves foráneas, restricciones UNIQUE,
    restricciones CHECK e índices sobre las tablas creadas en 02_tables.sql.

    Diseño a prueba de errores en cascada:
      - Todo el script es UN SOLO LOTE (sin GO). Si una validación falla,
        THROW detiene el script completo. Antes, con un GO por bloque, el
        THROW solo abortaba su lote y los ~40 lotes siguientes fallaban con
        "Invalid object name" y "column does not exist" (los ~75 errores).
      - Valida tablas y columnas antes de tocar nada.
      - Cada restricción/índice se crea solo si no existe con ese nombre
        (idempotente) y nunca elimina objetos ajenos.

    Requiere 01_database.sql y 02_tables.sql.
*/

USE [TecnoStock];
GO

SET NOCOUNT ON;
SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;

IF DB_NAME() <> N'TecnoStock'
BEGIN
    THROW 51000, N'Contexto de base de datos incorrecto. Ejecute 01_database.sql primero.', 1;
END;

/* ------------------------------------------------------------
   Validación previa: tablas requeridas
   ------------------------------------------------------------ */
IF  OBJECT_ID(N'dbo.Categorias', N'U') IS NULL
 OR OBJECT_ID(N'dbo.Usuarios', N'U') IS NULL
 OR OBJECT_ID(N'dbo.Productos', N'U') IS NULL
 OR OBJECT_ID(N'dbo.MovimientosInventario', N'U') IS NULL
BEGIN
    SELECT v.Tabla,
           CASE WHEN OBJECT_ID(N'dbo.' + v.Tabla, N'U') IS NULL
                THEN N'FALTA' ELSE N'OK' END AS Estado
    FROM (VALUES (N'Categorias'), (N'Usuarios'), (N'Productos'), (N'MovimientosInventario')) AS v (Tabla);

    THROW 51000, N'Faltan tablas. Ejecute 02_tables.sql antes de 03_constraints_indexes.sql.', 1;
END;

/* ------------------------------------------------------------
   Validación previa: columnas requeridas
   Evita "La columna X no existe" cuando hay un esquema viejo.
   ------------------------------------------------------------ */
DECLARE @columnas TABLE
(
    Tabla   SYSNAME NOT NULL,
    Columna SYSNAME NOT NULL,
    PRIMARY KEY (Tabla, Columna)
);

INSERT INTO @columnas (Tabla, Columna) VALUES
    (N'Categorias', N'CategoriaID'),
    (N'Categorias', N'Nombre'),
    (N'Categorias', N'Descripcion'),

    (N'Usuarios', N'UsuarioID'),
    (N'Usuarios', N'NombreUsuario'),
    (N'Usuarios', N'NombreCompleto'),
    (N'Usuarios', N'ClaveHash'),
    (N'Usuarios', N'Activo'),
    (N'Usuarios', N'FechaCreacion'),

    (N'Productos', N'ProductoID'),
    (N'Productos', N'Codigo'),
    (N'Productos', N'Nombre'),
    (N'Productos', N'Descripcion'),
    (N'Productos', N'CategoriaID'),
    (N'Productos', N'PrecioCompra'),
    (N'Productos', N'PrecioVenta'),
    (N'Productos', N'Stock'),
    (N'Productos', N'StockMinimo'),
    (N'Productos', N'Activo'),
    (N'Productos', N'FechaCreacion'),
    (N'Productos', N'FechaActualizacion'),

    (N'MovimientosInventario', N'MovimientoID'),
    (N'MovimientosInventario', N'ProductoID'),
    (N'MovimientosInventario', N'UsuarioID'),
    (N'MovimientosInventario', N'Tipo'),
    (N'MovimientosInventario', N'Cantidad'),
    (N'MovimientosInventario', N'Motivo'),
    (N'MovimientosInventario', N'StockAnterior'),
    (N'MovimientosInventario', N'StockPosterior'),
    (N'MovimientosInventario', N'Fecha');

IF EXISTS
(
    SELECT 1
    FROM @columnas AS e
    WHERE NOT EXISTS
          (
              SELECT 1
              FROM sys.columns AS c
              WHERE c.object_id = OBJECT_ID(N'dbo.' + e.Tabla, N'U')
                AND c.name = e.Columna
          )
)
BEGIN
    SELECT e.Tabla, e.Columna AS ColumnaFaltante
    FROM @columnas AS e
    WHERE NOT EXISTS
          (
              SELECT 1
              FROM sys.columns AS c
              WHERE c.object_id = OBJECT_ID(N'dbo.' + e.Tabla, N'U')
                AND c.name = e.Columna
          )
    ORDER BY e.Tabla, e.Columna;

    THROW 51001, N'Esquema incompatible: faltan columnas. Revise el resultado anterior. No se aplicó ningún cambio.', 1;
END;

/* ============================================================
   Claves primarias
   ============================================================ */

IF NOT EXISTS
(
    SELECT 1 FROM sys.key_constraints
    WHERE name = N'PK_Categorias'
      AND parent_object_id = OBJECT_ID(N'dbo.Categorias')
)
    ALTER TABLE dbo.Categorias
        ADD CONSTRAINT PK_Categorias PRIMARY KEY CLUSTERED (CategoriaID);

IF NOT EXISTS
(
    SELECT 1 FROM sys.key_constraints
    WHERE name = N'PK_Usuarios'
      AND parent_object_id = OBJECT_ID(N'dbo.Usuarios')
)
    ALTER TABLE dbo.Usuarios
        ADD CONSTRAINT PK_Usuarios PRIMARY KEY CLUSTERED (UsuarioID);

IF NOT EXISTS
(
    SELECT 1 FROM sys.key_constraints
    WHERE name = N'PK_Productos'
      AND parent_object_id = OBJECT_ID(N'dbo.Productos')
)
    ALTER TABLE dbo.Productos
        ADD CONSTRAINT PK_Productos PRIMARY KEY CLUSTERED (ProductoID);

IF NOT EXISTS
(
    SELECT 1 FROM sys.key_constraints
    WHERE name = N'PK_MovimientosInventario'
      AND parent_object_id = OBJECT_ID(N'dbo.MovimientosInventario')
)
    ALTER TABLE dbo.MovimientosInventario
        ADD CONSTRAINT PK_MovimientosInventario PRIMARY KEY CLUSTERED (MovimientoID);

/* ============================================================
   Restricciones UNIQUE
   ============================================================ */

IF NOT EXISTS
(
    SELECT 1 FROM sys.key_constraints
    WHERE name = N'UQ_Categorias_Nombre'
      AND parent_object_id = OBJECT_ID(N'dbo.Categorias')
)
    ALTER TABLE dbo.Categorias
        ADD CONSTRAINT UQ_Categorias_Nombre UNIQUE (Nombre);

IF NOT EXISTS
(
    SELECT 1 FROM sys.key_constraints
    WHERE name = N'UQ_Usuarios_NombreUsuario'
      AND parent_object_id = OBJECT_ID(N'dbo.Usuarios')
)
    ALTER TABLE dbo.Usuarios
        ADD CONSTRAINT UQ_Usuarios_NombreUsuario UNIQUE (NombreUsuario);

IF NOT EXISTS
(
    SELECT 1 FROM sys.key_constraints
    WHERE name = N'UQ_Productos_Codigo'
      AND parent_object_id = OBJECT_ID(N'dbo.Productos')
)
    ALTER TABLE dbo.Productos
        ADD CONSTRAINT UQ_Productos_Codigo UNIQUE (Codigo);

/* ============================================================
   Claves foráneas
   ============================================================ */

IF NOT EXISTS
(
    SELECT 1 FROM sys.foreign_keys
    WHERE name = N'FK_Productos_Categorias'
      AND parent_object_id = OBJECT_ID(N'dbo.Productos')
)
    ALTER TABLE dbo.Productos WITH CHECK
        ADD CONSTRAINT FK_Productos_Categorias
        FOREIGN KEY (CategoriaID)
        REFERENCES dbo.Categorias (CategoriaID)
        ON DELETE NO ACTION
        ON UPDATE NO ACTION;

IF NOT EXISTS
(
    SELECT 1 FROM sys.foreign_keys
    WHERE name = N'FK_MovimientosInventario_Productos'
      AND parent_object_id = OBJECT_ID(N'dbo.MovimientosInventario')
)
    ALTER TABLE dbo.MovimientosInventario WITH CHECK
        ADD CONSTRAINT FK_MovimientosInventario_Productos
        FOREIGN KEY (ProductoID)
        REFERENCES dbo.Productos (ProductoID)
        ON DELETE NO ACTION
        ON UPDATE NO ACTION;

IF NOT EXISTS
(
    SELECT 1 FROM sys.foreign_keys
    WHERE name = N'FK_MovimientosInventario_Usuarios'
      AND parent_object_id = OBJECT_ID(N'dbo.MovimientosInventario')
)
    ALTER TABLE dbo.MovimientosInventario WITH CHECK
        ADD CONSTRAINT FK_MovimientosInventario_Usuarios
        FOREIGN KEY (UsuarioID)
        REFERENCES dbo.Usuarios (UsuarioID)
        ON DELETE NO ACTION
        ON UPDATE NO ACTION;

/* ============================================================
   Restricciones CHECK
   ============================================================ */

IF NOT EXISTS
(
    SELECT 1 FROM sys.check_constraints
    WHERE name = N'CK_Categorias_Nombre_NoVacio'
      AND parent_object_id = OBJECT_ID(N'dbo.Categorias')
)
    ALTER TABLE dbo.Categorias WITH CHECK
        ADD CONSTRAINT CK_Categorias_Nombre_NoVacio
        CHECK (LEN(LTRIM(RTRIM(Nombre))) > 0);

IF NOT EXISTS
(
    SELECT 1 FROM sys.check_constraints
    WHERE name = N'CK_Productos_Codigo_NoVacio'
      AND parent_object_id = OBJECT_ID(N'dbo.Productos')
)
    ALTER TABLE dbo.Productos WITH CHECK
        ADD CONSTRAINT CK_Productos_Codigo_NoVacio
        CHECK (LEN(LTRIM(RTRIM(Codigo))) > 0);

IF NOT EXISTS
(
    SELECT 1 FROM sys.check_constraints
    WHERE name = N'CK_Productos_Nombre_NoVacio'
      AND parent_object_id = OBJECT_ID(N'dbo.Productos')
)
    ALTER TABLE dbo.Productos WITH CHECK
        ADD CONSTRAINT CK_Productos_Nombre_NoVacio
        CHECK (LEN(LTRIM(RTRIM(Nombre))) > 0);

IF NOT EXISTS
(
    SELECT 1 FROM sys.check_constraints
    WHERE name = N'CK_Productos_Descripcion_NoVacia'
      AND parent_object_id = OBJECT_ID(N'dbo.Productos')
)
    ALTER TABLE dbo.Productos WITH CHECK
        ADD CONSTRAINT CK_Productos_Descripcion_NoVacia
        CHECK (LEN(LTRIM(RTRIM(Descripcion))) > 0);

IF NOT EXISTS
(
    SELECT 1 FROM sys.check_constraints
    WHERE name = N'CK_Productos_PrecioCompra_Positivo'
      AND parent_object_id = OBJECT_ID(N'dbo.Productos')
)
    ALTER TABLE dbo.Productos WITH CHECK
        ADD CONSTRAINT CK_Productos_PrecioCompra_Positivo
        CHECK (PrecioCompra > 0);

IF NOT EXISTS
(
    SELECT 1 FROM sys.check_constraints
    WHERE name = N'CK_Productos_PrecioVenta_Positivo'
      AND parent_object_id = OBJECT_ID(N'dbo.Productos')
)
    ALTER TABLE dbo.Productos WITH CHECK
        ADD CONSTRAINT CK_Productos_PrecioVenta_Positivo
        CHECK (PrecioVenta > 0);

IF NOT EXISTS
(
    SELECT 1 FROM sys.check_constraints
    WHERE name = N'CK_Productos_Stock_NoNegativo'
      AND parent_object_id = OBJECT_ID(N'dbo.Productos')
)
    ALTER TABLE dbo.Productos WITH CHECK
        ADD CONSTRAINT CK_Productos_Stock_NoNegativo
        CHECK (Stock >= 0);

IF NOT EXISTS
(
    SELECT 1 FROM sys.check_constraints
    WHERE name = N'CK_Productos_StockMinimo_NoNegativo'
      AND parent_object_id = OBJECT_ID(N'dbo.Productos')
)
    ALTER TABLE dbo.Productos WITH CHECK
        ADD CONSTRAINT CK_Productos_StockMinimo_NoNegativo
        CHECK (StockMinimo >= 0);

IF NOT EXISTS
(
    SELECT 1 FROM sys.check_constraints
    WHERE name = N'CK_Usuarios_NombreUsuario_NoVacio'
      AND parent_object_id = OBJECT_ID(N'dbo.Usuarios')
)
    ALTER TABLE dbo.Usuarios WITH CHECK
        ADD CONSTRAINT CK_Usuarios_NombreUsuario_NoVacio
        CHECK (LEN(LTRIM(RTRIM(NombreUsuario))) > 0);

IF NOT EXISTS
(
    SELECT 1 FROM sys.check_constraints
    WHERE name = N'CK_Usuarios_NombreCompleto_NoVacio'
      AND parent_object_id = OBJECT_ID(N'dbo.Usuarios')
)
    ALTER TABLE dbo.Usuarios WITH CHECK
        ADD CONSTRAINT CK_Usuarios_NombreCompleto_NoVacio
        CHECK (LEN(LTRIM(RTRIM(NombreCompleto))) > 0);

IF NOT EXISTS
(
    SELECT 1 FROM sys.check_constraints
    WHERE name = N'CK_Usuarios_ClaveHash_NoVacia'
      AND parent_object_id = OBJECT_ID(N'dbo.Usuarios')
)
    ALTER TABLE dbo.Usuarios WITH CHECK
        ADD CONSTRAINT CK_Usuarios_ClaveHash_NoVacia
        CHECK (LEN(LTRIM(RTRIM(ClaveHash))) > 0);

IF NOT EXISTS
(
    SELECT 1 FROM sys.check_constraints
    WHERE name = N'CK_MovimientosInventario_Tipo_Valido'
      AND parent_object_id = OBJECT_ID(N'dbo.MovimientosInventario')
)
    ALTER TABLE dbo.MovimientosInventario WITH CHECK
        ADD CONSTRAINT CK_MovimientosInventario_Tipo_Valido
        CHECK (Tipo IN ('ENTRADA', 'SALIDA'));

IF NOT EXISTS
(
    SELECT 1 FROM sys.check_constraints
    WHERE name = N'CK_MovimientosInventario_Cantidad_Positiva'
      AND parent_object_id = OBJECT_ID(N'dbo.MovimientosInventario')
)
    ALTER TABLE dbo.MovimientosInventario WITH CHECK
        ADD CONSTRAINT CK_MovimientosInventario_Cantidad_Positiva
        CHECK (Cantidad > 0);

IF NOT EXISTS
(
    SELECT 1 FROM sys.check_constraints
    WHERE name = N'CK_MovimientosInventario_Motivo_NoVacio'
      AND parent_object_id = OBJECT_ID(N'dbo.MovimientosInventario')
)
    ALTER TABLE dbo.MovimientosInventario WITH CHECK
        ADD CONSTRAINT CK_MovimientosInventario_Motivo_NoVacio
        CHECK (LEN(LTRIM(RTRIM(Motivo))) > 0);

IF NOT EXISTS
(
    SELECT 1 FROM sys.check_constraints
    WHERE name = N'CK_MovimientosInventario_Stock_NoNegativo'
      AND parent_object_id = OBJECT_ID(N'dbo.MovimientosInventario')
)
    ALTER TABLE dbo.MovimientosInventario WITH CHECK
        ADD CONSTRAINT CK_MovimientosInventario_Stock_NoNegativo
        CHECK (StockAnterior >= 0 AND StockPosterior >= 0);

IF NOT EXISTS
(
    SELECT 1 FROM sys.check_constraints
    WHERE name = N'CK_MovimientosInventario_Stock_Consistente'
      AND parent_object_id = OBJECT_ID(N'dbo.MovimientosInventario')
)
    ALTER TABLE dbo.MovimientosInventario WITH CHECK
        ADD CONSTRAINT CK_MovimientosInventario_Stock_Consistente
        CHECK
        (
            (Tipo = 'ENTRADA' AND StockPosterior = StockAnterior + Cantidad)
            OR
            (Tipo = 'SALIDA' AND StockPosterior = StockAnterior - Cantidad)
        );

/* ============================================================
   Índices de apoyo
   ============================================================ */

IF NOT EXISTS
(
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_Productos_CategoriaID'
      AND object_id = OBJECT_ID(N'dbo.Productos')
)
    CREATE NONCLUSTERED INDEX IX_Productos_CategoriaID
        ON dbo.Productos (CategoriaID);

IF NOT EXISTS
(
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_Productos_Activo_Stock'
      AND object_id = OBJECT_ID(N'dbo.Productos')
)
    CREATE NONCLUSTERED INDEX IX_Productos_Activo_Stock
        ON dbo.Productos (Activo, Stock)
        INCLUDE (StockMinimo, PrecioCompra, PrecioVenta, CategoriaID);

IF NOT EXISTS
(
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_MovimientosInventario_Producto_Fecha'
      AND object_id = OBJECT_ID(N'dbo.MovimientosInventario')
)
    CREATE NONCLUSTERED INDEX IX_MovimientosInventario_Producto_Fecha
        ON dbo.MovimientosInventario (ProductoID, Fecha DESC);

IF NOT EXISTS
(
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_MovimientosInventario_Fecha'
      AND object_id = OBJECT_ID(N'dbo.MovimientosInventario')
)
    CREATE NONCLUSTERED INDEX IX_MovimientosInventario_Fecha
        ON dbo.MovimientosInventario (Fecha DESC);

IF NOT EXISTS
(
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_MovimientosInventario_UsuarioID'
      AND object_id = OBJECT_ID(N'dbo.MovimientosInventario')
)
    CREATE NONCLUSTERED INDEX IX_MovimientosInventario_UsuarioID
        ON dbo.MovimientosInventario (UsuarioID);

PRINT N'03_constraints_indexes.sql finalizado: restricciones e índices verificados.';
GO
