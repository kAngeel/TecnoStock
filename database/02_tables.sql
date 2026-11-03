/*
    TecnoStock - 02_tables.sql
    Crea las tablas base del sistema.

    Comportamiento:
      - Solo crea tablas que no existen (IF OBJECT_ID(...) IS NULL).
      - NO modifica tablas existentes: no agrega ni cambia columnas, tipos,
        DEFAULT ni restricciones. Si una tabla ya existe, se omite.
      - Antes de crear nada valida que las tablas existentes tengan todas
        las columnas esperadas. Si falta alguna, aborta con UN solo error
        claro (en lugar de dejar decenas de errores en cascada).

    Todo el cuerpo va en un único lote (sin GO) para que un THROW detenga
    el script por completo.

    No crea usuarios, credenciales ni datos de prueba.
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
   Columnas mínimas esperadas por tabla.
   Sirve para detectar esquemas viejos o incompletos antes de seguir.
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
    WHERE OBJECT_ID(N'dbo.' + e.Tabla, N'U') IS NOT NULL
      AND NOT EXISTS
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
    WHERE OBJECT_ID(N'dbo.' + e.Tabla, N'U') IS NOT NULL
      AND NOT EXISTS
          (
              SELECT 1
              FROM sys.columns AS c
              WHERE c.object_id = OBJECT_ID(N'dbo.' + e.Tabla, N'U')
                AND c.name = e.Columna
          )
    ORDER BY e.Tabla, e.Columna;

    THROW 51001, N'Esquema incompatible: faltan columnas en tablas existentes. Revise el resultado anterior. Este script no modifica tablas ya creadas.', 1;
END;

/* ------------------------------------------------------------
   Tablas
   ------------------------------------------------------------ */

IF OBJECT_ID(N'dbo.Categorias', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Categorias
    (
        CategoriaID INT IDENTITY(1,1) NOT NULL,
        Nombre NVARCHAR(100) NOT NULL,
        Descripcion NVARCHAR(300) NULL
    );
    PRINT N'Tabla dbo.Categorias creada.';
END;

IF OBJECT_ID(N'dbo.Usuarios', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Usuarios
    (
        UsuarioID INT IDENTITY(1,1) NOT NULL,
        NombreUsuario NVARCHAR(50) NOT NULL,
        NombreCompleto NVARCHAR(150) NOT NULL,
        ClaveHash NVARCHAR(255) NOT NULL,
        Activo BIT NOT NULL
            CONSTRAINT DF_Usuarios_Activo DEFAULT (1),
        FechaCreacion DATETIME2(0) NOT NULL
            CONSTRAINT DF_Usuarios_FechaCreacion DEFAULT (SYSDATETIME())
    );
    PRINT N'Tabla dbo.Usuarios creada.';
END;

IF OBJECT_ID(N'dbo.Productos', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Productos
    (
        ProductoID INT IDENTITY(1,1) NOT NULL,
        Codigo NVARCHAR(50) NOT NULL,
        Nombre NVARCHAR(150) NOT NULL,
        Descripcion NVARCHAR(500) NOT NULL,
        CategoriaID INT NOT NULL,
        PrecioCompra DECIMAL(12,2) NOT NULL,
        PrecioVenta DECIMAL(12,2) NOT NULL,
        Stock INT NOT NULL
            CONSTRAINT DF_Productos_Stock DEFAULT (0),
        StockMinimo INT NOT NULL
            CONSTRAINT DF_Productos_StockMinimo DEFAULT (0),
        Activo BIT NOT NULL
            CONSTRAINT DF_Productos_Activo DEFAULT (1),
        FechaCreacion DATETIME2(0) NOT NULL
            CONSTRAINT DF_Productos_FechaCreacion DEFAULT (SYSDATETIME()),
        FechaActualizacion DATETIME2(0) NOT NULL
            CONSTRAINT DF_Productos_FechaActualizacion DEFAULT (SYSDATETIME())
    );
    PRINT N'Tabla dbo.Productos creada.';
END;

IF OBJECT_ID(N'dbo.MovimientosInventario', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.MovimientosInventario
    (
        MovimientoID BIGINT IDENTITY(1,1) NOT NULL,
        ProductoID INT NOT NULL,
        UsuarioID INT NOT NULL,
        Tipo VARCHAR(10) NOT NULL,
        Cantidad INT NOT NULL,
        Motivo NVARCHAR(200) NOT NULL,
        StockAnterior INT NOT NULL,
        StockPosterior INT NOT NULL,
        Fecha DATETIME2(0) NOT NULL
            CONSTRAINT DF_MovimientosInventario_Fecha DEFAULT (SYSDATETIME())
    );
    PRINT N'Tabla dbo.MovimientosInventario creada.';
END;

PRINT N'02_tables.sql finalizado. Las tablas existentes no se modificaron.';
GO
