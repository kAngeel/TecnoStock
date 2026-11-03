/*
    TecnoStock - 04_procedures.sql
    Procedimientos almacenados del sistema.

    Reglas de diseño:
      - Toda lectura y escritura de la aplicación pasa por estos procedimientos.
      - Ningún procedimiento de productos permite fijar o modificar Stock:
        el stock solo cambia con los procedimientos de entrada y salida.
      - Entradas y salidas usan transacción explícita, XACT_ABORT y bloqueo
        UPDLOCK/ROWLOCK sobre la fila del producto, de modo que dos salidas
        simultáneas no pueden dejar stock negativo.
      - El historial (MovimientosInventario) es de solo inserción.
      - Los errores de negocio se lanzan con THROW y códigos 500xx, que el
        backend traduce a respuestas HTTP concretas.

    Orden: ejecutar después de 01, 02 y 03.
*/

USE [TecnoStock];
GO

SET NOCOUNT ON;
SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

IF DB_NAME() <> N'TecnoStock'
BEGIN
    THROW 51000, N'Contexto de base de datos incorrecto. Ejecute 01_database.sql primero.', 1;
END;
GO

/* ============================================================
   USUARIOS / AUTENTICACIÓN
   ============================================================ */

CREATE OR ALTER PROCEDURE dbo.usp_Usuarios_ObtenerPorNombreUsuario
    @NombreUsuario NVARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;

    SELECT
        UsuarioID,
        NombreUsuario,
        NombreCompleto,
        ClaveHash,
        Activo,
        FechaCreacion
    FROM dbo.Usuarios
    WHERE NombreUsuario = @NombreUsuario;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_Usuarios_ObtenerPorID
    @UsuarioID INT
AS
BEGIN
    SET NOCOUNT ON;

    SELECT
        UsuarioID,
        NombreUsuario,
        NombreCompleto,
        Activo,
        FechaCreacion
    FROM dbo.Usuarios
    WHERE UsuarioID = @UsuarioID;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_Usuarios_Insertar
    @NombreUsuario  NVARCHAR(50),
    @NombreCompleto NVARCHAR(150),
    @ClaveHash      NVARCHAR(255),
    @UsuarioID      INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    IF @NombreUsuario IS NULL OR LEN(LTRIM(RTRIM(@NombreUsuario))) = 0
        THROW 50001, N'El nombre de usuario es obligatorio.', 1;

    IF @NombreCompleto IS NULL OR LEN(LTRIM(RTRIM(@NombreCompleto))) = 0
        THROW 50002, N'El nombre completo es obligatorio.', 1;

    IF @ClaveHash IS NULL OR LEN(LTRIM(RTRIM(@ClaveHash))) = 0
        THROW 50003, N'El hash de la contraseña es obligatorio.', 1;

    IF EXISTS (SELECT 1 FROM dbo.Usuarios WHERE NombreUsuario = @NombreUsuario)
        THROW 50004, N'Ya existe un usuario con ese nombre de usuario.', 1;

    INSERT INTO dbo.Usuarios (NombreUsuario, NombreCompleto, ClaveHash, Activo)
    VALUES (@NombreUsuario, @NombreCompleto, @ClaveHash, 1);

    SET @UsuarioID = CAST(SCOPE_IDENTITY() AS INT);
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_Usuarios_Listar
AS
BEGIN
    SET NOCOUNT ON;

    SELECT
        UsuarioID,
        NombreUsuario,
        NombreCompleto,
        Activo,
        FechaCreacion
    FROM dbo.Usuarios
    ORDER BY NombreUsuario;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_Usuarios_ActualizarClaveHash
    @UsuarioID INT,
    @ClaveHash NVARCHAR(255)
AS
BEGIN
    SET NOCOUNT ON;

    IF @ClaveHash IS NULL OR LEN(LTRIM(RTRIM(@ClaveHash))) = 0
        THROW 50003, N'El hash de la contraseña es obligatorio.', 1;

    UPDATE dbo.Usuarios
       SET ClaveHash = @ClaveHash
     WHERE UsuarioID = @UsuarioID;

    IF @@ROWCOUNT = 0
        THROW 50005, N'Usuario no encontrado.', 1;
END;
GO

/* ============================================================
   CATEGORÍAS
   ============================================================ */

CREATE OR ALTER PROCEDURE dbo.usp_Categorias_Listar
AS
BEGIN
    SET NOCOUNT ON;

    SELECT
        c.CategoriaID,
        c.Nombre,
        c.Descripcion,
        (
            SELECT COUNT(*)
            FROM dbo.Productos AS p
            WHERE p.CategoriaID = c.CategoriaID
        ) AS TotalProductos
    FROM dbo.Categorias AS c
    ORDER BY c.Nombre;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_Categorias_Obtener
    @CategoriaID INT
AS
BEGIN
    SET NOCOUNT ON;

    SELECT
        c.CategoriaID,
        c.Nombre,
        c.Descripcion,
        (
            SELECT COUNT(*)
            FROM dbo.Productos AS p
            WHERE p.CategoriaID = c.CategoriaID
        ) AS TotalProductos
    FROM dbo.Categorias AS c
    WHERE c.CategoriaID = @CategoriaID;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_Categorias_Insertar
    @Nombre      NVARCHAR(100),
    @Descripcion NVARCHAR(300) = NULL,
    @CategoriaID INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    SET @Nombre = LTRIM(RTRIM(@Nombre));

    IF @Nombre IS NULL OR LEN(@Nombre) = 0
        THROW 50010, N'El nombre de la categoría es obligatorio.', 1;

    IF EXISTS (SELECT 1 FROM dbo.Categorias WHERE Nombre = @Nombre)
        THROW 50011, N'Ya existe una categoría con ese nombre.', 1;

    INSERT INTO dbo.Categorias (Nombre, Descripcion)
    VALUES (@Nombre, NULLIF(LTRIM(RTRIM(@Descripcion)), N''));

    SET @CategoriaID = CAST(SCOPE_IDENTITY() AS INT);
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_Categorias_Actualizar
    @CategoriaID INT,
    @Nombre      NVARCHAR(100),
    @Descripcion NVARCHAR(300) = NULL
AS
BEGIN
    SET NOCOUNT ON;

    SET @Nombre = LTRIM(RTRIM(@Nombre));

    IF @Nombre IS NULL OR LEN(@Nombre) = 0
        THROW 50010, N'El nombre de la categoría es obligatorio.', 1;

    IF NOT EXISTS (SELECT 1 FROM dbo.Categorias WHERE CategoriaID = @CategoriaID)
        THROW 50012, N'Categoría no encontrada.', 1;

    IF EXISTS (SELECT 1 FROM dbo.Categorias WHERE Nombre = @Nombre AND CategoriaID <> @CategoriaID)
        THROW 50011, N'Ya existe una categoría con ese nombre.', 1;

    UPDATE dbo.Categorias
       SET Nombre = @Nombre,
           Descripcion = NULLIF(LTRIM(RTRIM(@Descripcion)), N'')
     WHERE CategoriaID = @CategoriaID;
END;
GO

/* ============================================================
   PRODUCTOS
   El stock NO se recibe ni se actualiza en estos procedimientos.
   ============================================================ */

CREATE OR ALTER PROCEDURE dbo.usp_Productos_Listar
    @Busqueda    NVARCHAR(150) = NULL,
    @CategoriaID INT = NULL,
    @SoloActivos BIT = 1
AS
BEGIN
    SET NOCOUNT ON;

    SET @Busqueda = NULLIF(LTRIM(RTRIM(@Busqueda)), N'');

    SELECT
        p.ProductoID,
        p.Codigo,
        p.Nombre,
        p.Descripcion,
        p.CategoriaID,
        c.Nombre AS CategoriaNombre,
        p.PrecioCompra,
        p.PrecioVenta,
        p.Stock,
        p.StockMinimo,
        p.Activo,
        p.FechaCreacion,
        p.FechaActualizacion,
        CAST(p.Stock * p.PrecioCompra AS DECIMAL(18,2)) AS ValorInventario,
        CASE WHEN p.Stock <= p.StockMinimo THEN CAST(1 AS BIT) ELSE CAST(0 AS BIT) END AS StockBajo
    FROM dbo.Productos AS p
    INNER JOIN dbo.Categorias AS c
            ON c.CategoriaID = p.CategoriaID
    WHERE (@CategoriaID IS NULL OR p.CategoriaID = @CategoriaID)
      AND (@SoloActivos = 0 OR p.Activo = 1)
      AND (
            @Busqueda IS NULL
            OR p.Codigo LIKE N'%' + @Busqueda + N'%'
            OR p.Nombre LIKE N'%' + @Busqueda + N'%'
          )
    ORDER BY p.Nombre;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_Productos_Obtener
    @ProductoID INT
AS
BEGIN
    SET NOCOUNT ON;

    SELECT
        p.ProductoID,
        p.Codigo,
        p.Nombre,
        p.Descripcion,
        p.CategoriaID,
        c.Nombre AS CategoriaNombre,
        p.PrecioCompra,
        p.PrecioVenta,
        p.Stock,
        p.StockMinimo,
        p.Activo,
        p.FechaCreacion,
        p.FechaActualizacion,
        CAST(p.Stock * p.PrecioCompra AS DECIMAL(18,2)) AS ValorInventario,
        CASE WHEN p.Stock <= p.StockMinimo THEN CAST(1 AS BIT) ELSE CAST(0 AS BIT) END AS StockBajo
    FROM dbo.Productos AS p
    INNER JOIN dbo.Categorias AS c
            ON c.CategoriaID = p.CategoriaID
    WHERE p.ProductoID = @ProductoID;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_Productos_Insertar
    @Codigo       NVARCHAR(50),
    @Nombre       NVARCHAR(150),
    @Descripcion  NVARCHAR(500),
    @CategoriaID  INT,
    @PrecioCompra DECIMAL(12,2),
    @PrecioVenta  DECIMAL(12,2),
    @StockMinimo  INT,
    @Activo       BIT,
    @ProductoID   INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    SET @Codigo = LTRIM(RTRIM(@Codigo));
    SET @Nombre = LTRIM(RTRIM(@Nombre));
    SET @Descripcion = LTRIM(RTRIM(@Descripcion));

    IF @Codigo IS NULL OR LEN(@Codigo) = 0
        THROW 50020, N'El código del producto es obligatorio.', 1;

    IF @Nombre IS NULL OR LEN(@Nombre) = 0
        THROW 50021, N'El nombre del producto es obligatorio.', 1;

    IF @Descripcion IS NULL OR LEN(@Descripcion) = 0
        THROW 50022, N'La descripción del producto es obligatoria.', 1;

    IF @PrecioCompra IS NULL OR @PrecioCompra <= 0
        THROW 50023, N'El precio de compra debe ser mayor que cero.', 1;

    IF @PrecioVenta IS NULL OR @PrecioVenta <= 0
        THROW 50024, N'El precio de venta debe ser mayor que cero.', 1;

    IF @StockMinimo IS NULL OR @StockMinimo < 0
        THROW 50025, N'El stock mínimo no puede ser negativo.', 1;

    IF NOT EXISTS (SELECT 1 FROM dbo.Categorias WHERE CategoriaID = @CategoriaID)
        THROW 50026, N'La categoría indicada no existe.', 1;

    IF EXISTS (SELECT 1 FROM dbo.Productos WHERE Codigo = @Codigo)
        THROW 50027, N'Ya existe un producto con ese código.', 1;

    /* Stock deliberadamente ausente: la columna usa DEFAULT (0). */
    INSERT INTO dbo.Productos
    (
        Codigo,
        Nombre,
        Descripcion,
        CategoriaID,
        PrecioCompra,
        PrecioVenta,
        StockMinimo,
        Activo
    )
    VALUES
    (
        @Codigo,
        @Nombre,
        @Descripcion,
        @CategoriaID,
        @PrecioCompra,
        @PrecioVenta,
        @StockMinimo,
        ISNULL(@Activo, 1)
    );

    SET @ProductoID = CAST(SCOPE_IDENTITY() AS INT);
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_Productos_Actualizar
    @ProductoID   INT,
    @Codigo       NVARCHAR(50),
    @Nombre       NVARCHAR(150),
    @Descripcion  NVARCHAR(500),
    @CategoriaID  INT,
    @PrecioCompra DECIMAL(12,2),
    @PrecioVenta  DECIMAL(12,2),
    @StockMinimo  INT,
    @Activo       BIT
AS
BEGIN
    SET NOCOUNT ON;

    SET @Codigo = LTRIM(RTRIM(@Codigo));
    SET @Nombre = LTRIM(RTRIM(@Nombre));
    SET @Descripcion = LTRIM(RTRIM(@Descripcion));

    IF NOT EXISTS (SELECT 1 FROM dbo.Productos WHERE ProductoID = @ProductoID)
        THROW 50028, N'Producto no encontrado.', 1;

    IF @Codigo IS NULL OR LEN(@Codigo) = 0
        THROW 50020, N'El código del producto es obligatorio.', 1;

    IF @Nombre IS NULL OR LEN(@Nombre) = 0
        THROW 50021, N'El nombre del producto es obligatorio.', 1;

    IF @Descripcion IS NULL OR LEN(@Descripcion) = 0
        THROW 50022, N'La descripción del producto es obligatoria.', 1;

    IF @PrecioCompra IS NULL OR @PrecioCompra <= 0
        THROW 50023, N'El precio de compra debe ser mayor que cero.', 1;

    IF @PrecioVenta IS NULL OR @PrecioVenta <= 0
        THROW 50024, N'El precio de venta debe ser mayor que cero.', 1;

    IF @StockMinimo IS NULL OR @StockMinimo < 0
        THROW 50025, N'El stock mínimo no puede ser negativo.', 1;

    IF NOT EXISTS (SELECT 1 FROM dbo.Categorias WHERE CategoriaID = @CategoriaID)
        THROW 50026, N'La categoría indicada no existe.', 1;

    IF EXISTS (SELECT 1 FROM dbo.Productos WHERE Codigo = @Codigo AND ProductoID <> @ProductoID)
        THROW 50027, N'Ya existe otro producto con ese código.', 1;

    /* Stock deliberadamente ausente: solo cambia con movimientos. */
    UPDATE dbo.Productos
       SET Codigo = @Codigo,
           Nombre = @Nombre,
           Descripcion = @Descripcion,
           CategoriaID = @CategoriaID,
           PrecioCompra = @PrecioCompra,
           PrecioVenta = @PrecioVenta,
           StockMinimo = @StockMinimo,
           Activo = ISNULL(@Activo, Activo),
           FechaActualizacion = SYSDATETIME()
     WHERE ProductoID = @ProductoID;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_Productos_Desactivar
    @ProductoID INT
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE dbo.Productos
       SET Activo = 0,
           FechaActualizacion = SYSDATETIME()
     WHERE ProductoID = @ProductoID;

    IF @@ROWCOUNT = 0
        THROW 50028, N'Producto no encontrado.', 1;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_Productos_Activar
    @ProductoID INT
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE dbo.Productos
       SET Activo = 1,
           FechaActualizacion = SYSDATETIME()
     WHERE ProductoID = @ProductoID;

    IF @@ROWCOUNT = 0
        THROW 50028, N'Producto no encontrado.', 1;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_Productos_StockBajo
AS
BEGIN
    SET NOCOUNT ON;

    /* Solo productos activos, según lo aprobado. */
    SELECT
        p.ProductoID,
        p.Codigo,
        p.Nombre,
        p.CategoriaID,
        c.Nombre AS CategoriaNombre,
        p.Stock,
        p.StockMinimo,
        (p.StockMinimo - p.Stock) AS Faltante,
        p.PrecioCompra
    FROM dbo.Productos AS p
    INNER JOIN dbo.Categorias AS c
            ON c.CategoriaID = p.CategoriaID
    WHERE p.Activo = 1
      AND p.Stock <= p.StockMinimo
    ORDER BY (p.StockMinimo - p.Stock) DESC, p.Nombre;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_Productos_ValorInventario
AS
BEGIN
    SET NOCOUNT ON;

    /* Incluye productos inactivos con existencias físicas, según lo aprobado. */
    SELECT
        ISNULL(SUM(CAST(p.Stock AS DECIMAL(18,2)) * p.PrecioCompra), 0) AS ValorInventario,
        ISNULL(SUM(p.Stock), 0) AS UnidadesEnStock,
        COUNT(*) AS ProductosConStock
    FROM dbo.Productos AS p
    WHERE p.Stock > 0;
END;
GO

/* ============================================================
   MOVIMIENTOS DE INVENTARIO
   ============================================================ */

CREATE OR ALTER PROCEDURE dbo.usp_MovimientosInventario_RegistrarEntrada
    @ProductoID      INT,
    @UsuarioID       INT,
    @Cantidad        INT,
    @Motivo          NVARCHAR(200),
    @MovimientoID    BIGINT OUTPUT,
    @StockPosterior  INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    SET @Motivo = LTRIM(RTRIM(@Motivo));

    IF @Cantidad IS NULL OR @Cantidad <= 0
        THROW 50030, N'La cantidad debe ser mayor que cero.', 1;

    IF @Motivo IS NULL OR LEN(@Motivo) = 0
        THROW 50031, N'El motivo del movimiento es obligatorio.', 1;

    IF NOT EXISTS (SELECT 1 FROM dbo.Usuarios WHERE UsuarioID = @UsuarioID AND Activo = 1)
        THROW 50032, N'El usuario no existe o está inactivo.', 1;

    DECLARE @StockAnterior INT;

    BEGIN TRY
        BEGIN TRANSACTION;

        SELECT @StockAnterior = p.Stock
        FROM dbo.Productos AS p WITH (UPDLOCK, ROWLOCK)
        WHERE p.ProductoID = @ProductoID
          AND p.Activo = 1;

        IF @StockAnterior IS NULL
            THROW 50033, N'El producto no existe o está inactivo.', 1;

        SET @StockPosterior = @StockAnterior + @Cantidad;

        UPDATE dbo.Productos
           SET Stock = @StockPosterior,
               FechaActualizacion = SYSDATETIME()
         WHERE ProductoID = @ProductoID;

        INSERT INTO dbo.MovimientosInventario
        (
            ProductoID,
            UsuarioID,
            Tipo,
            Cantidad,
            Motivo,
            StockAnterior,
            StockPosterior,
            Fecha
        )
        VALUES
        (
            @ProductoID,
            @UsuarioID,
            'ENTRADA',
            @Cantidad,
            @Motivo,
            @StockAnterior,
            @StockPosterior,
            SYSDATETIME()
        );

        SET @MovimientoID = CAST(SCOPE_IDENTITY() AS BIGINT);

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF XACT_STATE() <> 0
            ROLLBACK TRANSACTION;
        THROW;
    END CATCH;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_MovimientosInventario_RegistrarSalida
    @ProductoID      INT,
    @UsuarioID       INT,
    @Cantidad        INT,
    @Motivo          NVARCHAR(200),
    @MovimientoID    BIGINT OUTPUT,
    @StockPosterior  INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    SET @Motivo = LTRIM(RTRIM(@Motivo));

    IF @Cantidad IS NULL OR @Cantidad <= 0
        THROW 50030, N'La cantidad debe ser mayor que cero.', 1;

    IF @Motivo IS NULL OR LEN(@Motivo) = 0
        THROW 50031, N'El motivo del movimiento es obligatorio.', 1;

    IF NOT EXISTS (SELECT 1 FROM dbo.Usuarios WHERE UsuarioID = @UsuarioID AND Activo = 1)
        THROW 50032, N'El usuario no existe o está inactivo.', 1;

    DECLARE @StockAnterior INT;

    BEGIN TRY
        BEGIN TRANSACTION;

        /* Bloqueo de actualización sobre la fila: serializa salidas concurrentes. */
        SELECT @StockAnterior = p.Stock
        FROM dbo.Productos AS p WITH (UPDLOCK, ROWLOCK)
        WHERE p.ProductoID = @ProductoID
          AND p.Activo = 1;

        IF @StockAnterior IS NULL
            THROW 50033, N'El producto no existe o está inactivo.', 1;

        IF @StockAnterior < @Cantidad
            THROW 50034, N'Stock insuficiente para realizar la salida.', 1;

        SET @StockPosterior = @StockAnterior - @Cantidad;

        UPDATE dbo.Productos
           SET Stock = @StockPosterior,
               FechaActualizacion = SYSDATETIME()
         WHERE ProductoID = @ProductoID;

        INSERT INTO dbo.MovimientosInventario
        (
            ProductoID,
            UsuarioID,
            Tipo,
            Cantidad,
            Motivo,
            StockAnterior,
            StockPosterior,
            Fecha
        )
        VALUES
        (
            @ProductoID,
            @UsuarioID,
            'SALIDA',
            @Cantidad,
            @Motivo,
            @StockAnterior,
            @StockPosterior,
            SYSDATETIME()
        );

        SET @MovimientoID = CAST(SCOPE_IDENTITY() AS BIGINT);

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF XACT_STATE() <> 0
            ROLLBACK TRANSACTION;
        THROW;
    END CATCH;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_MovimientosInventario_Listar
    @FechaDesde   DATE = NULL,
    @FechaHasta   DATE = NULL,
    @ProductoID   INT = NULL,
    @Tipo         VARCHAR(10) = NULL,
    @Pagina       INT = 1,
    @TamanoPagina INT = 20
AS
BEGIN
    SET NOCOUNT ON;

    IF @Pagina IS NULL OR @Pagina < 1
        SET @Pagina = 1;

    IF @TamanoPagina IS NULL OR @TamanoPagina < 1
        SET @TamanoPagina = 20;

    IF @TamanoPagina > 200
        SET @TamanoPagina = 200;

    IF @Tipo IS NOT NULL AND @Tipo NOT IN ('ENTRADA', 'SALIDA')
        THROW 50035, N'Tipo de movimiento inválido.', 1;

    SELECT
        m.MovimientoID,
        m.ProductoID,
        p.Codigo AS ProductoCodigo,
        p.Nombre AS ProductoNombre,
        m.UsuarioID,
        u.NombreUsuario,
        u.NombreCompleto AS UsuarioNombreCompleto,
        m.Tipo,
        m.Cantidad,
        m.Motivo,
        m.StockAnterior,
        m.StockPosterior,
        m.Fecha,
        COUNT(*) OVER () AS TotalFilas
    FROM dbo.MovimientosInventario AS m
    INNER JOIN dbo.Productos AS p
            ON p.ProductoID = m.ProductoID
    INNER JOIN dbo.Usuarios AS u
            ON u.UsuarioID = m.UsuarioID
    WHERE (@ProductoID IS NULL OR m.ProductoID = @ProductoID)
      AND (@Tipo IS NULL OR m.Tipo = @Tipo)
      AND (@FechaDesde IS NULL OR m.Fecha >= CAST(@FechaDesde AS DATETIME2(0)))
      AND (@FechaHasta IS NULL OR m.Fecha < DATEADD(DAY, 1, CAST(@FechaHasta AS DATETIME2(0))))
    ORDER BY m.Fecha DESC, m.MovimientoID DESC
    OFFSET (@Pagina - 1) * @TamanoPagina ROWS
    FETCH NEXT @TamanoPagina ROWS ONLY;
END;
GO

/* ============================================================
   DASHBOARD
   ============================================================ */

CREATE OR ALTER PROCEDURE dbo.usp_Dashboard_Resumen
    @FechaDesde DATE = NULL,
    @FechaHasta DATE = NULL
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @Desde DATETIME2(0) =
        CASE WHEN @FechaDesde IS NULL THEN NULL ELSE CAST(@FechaDesde AS DATETIME2(0)) END;

    DECLARE @Hasta DATETIME2(0) =
        CASE WHEN @FechaHasta IS NULL THEN NULL ELSE DATEADD(DAY, 1, CAST(@FechaHasta AS DATETIME2(0))) END;

    SELECT
        (SELECT COUNT(*) FROM dbo.Productos WHERE Activo = 1) AS ProductosActivos,
        (SELECT COUNT(*) FROM dbo.Productos WHERE Activo = 0) AS ProductosInactivos,
        (SELECT COUNT(*) FROM dbo.Productos) AS ProductosTotal,
        (SELECT COUNT(*) FROM dbo.Categorias) AS CategoriasTotal,
        (SELECT COUNT(*) FROM dbo.Productos WHERE Activo = 1 AND Stock <= StockMinimo) AS ProductosStockBajo,
        (SELECT ISNULL(SUM(CAST(Stock AS DECIMAL(18,2)) * PrecioCompra), 0)
           FROM dbo.Productos WHERE Stock > 0) AS ValorInventario,
        (SELECT ISNULL(SUM(Stock), 0) FROM dbo.Productos) AS UnidadesEnStock,
        (SELECT COUNT(*) FROM dbo.MovimientosInventario
          WHERE (@Desde IS NULL OR Fecha >= @Desde)
            AND (@Hasta IS NULL OR Fecha < @Hasta)) AS MovimientosPeriodo,
        (SELECT ISNULL(SUM(Cantidad), 0) FROM dbo.MovimientosInventario
          WHERE Tipo = 'ENTRADA'
            AND (@Desde IS NULL OR Fecha >= @Desde)
            AND (@Hasta IS NULL OR Fecha < @Hasta)) AS UnidadesEntrada,
        (SELECT ISNULL(SUM(Cantidad), 0) FROM dbo.MovimientosInventario
          WHERE Tipo = 'SALIDA'
            AND (@Desde IS NULL OR Fecha >= @Desde)
            AND (@Hasta IS NULL OR Fecha < @Hasta)) AS UnidadesSalida;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_Dashboard_MovimientosPorDia
    @FechaDesde DATE = NULL,
    @FechaHasta DATE = NULL
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @Desde DATETIME2(0) =
        CASE WHEN @FechaDesde IS NULL THEN NULL ELSE CAST(@FechaDesde AS DATETIME2(0)) END;

    DECLARE @Hasta DATETIME2(0) =
        CASE WHEN @FechaHasta IS NULL THEN NULL ELSE DATEADD(DAY, 1, CAST(@FechaHasta AS DATETIME2(0))) END;

    SELECT
        CAST(m.Fecha AS DATE) AS Fecha,
        ISNULL(SUM(CASE WHEN m.Tipo = 'ENTRADA' THEN m.Cantidad ELSE 0 END), 0) AS UnidadesEntrada,
        ISNULL(SUM(CASE WHEN m.Tipo = 'SALIDA' THEN m.Cantidad ELSE 0 END), 0) AS UnidadesSalida,
        COUNT(*) AS Movimientos
    FROM dbo.MovimientosInventario AS m
    WHERE (@Desde IS NULL OR m.Fecha >= @Desde)
      AND (@Hasta IS NULL OR m.Fecha < @Hasta)
    GROUP BY CAST(m.Fecha AS DATE)
    ORDER BY Fecha;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_Dashboard_TopProductos
    @FechaDesde DATE = NULL,
    @FechaHasta DATE = NULL,
    @Top        INT = 5
AS
BEGIN
    SET NOCOUNT ON;

    IF @Top IS NULL OR @Top < 1
        SET @Top = 5;

    IF @Top > 50
        SET @Top = 50;

    DECLARE @Desde DATETIME2(0) =
        CASE WHEN @FechaDesde IS NULL THEN NULL ELSE CAST(@FechaDesde AS DATETIME2(0)) END;

    DECLARE @Hasta DATETIME2(0) =
        CASE WHEN @FechaHasta IS NULL THEN NULL ELSE DATEADD(DAY, 1, CAST(@FechaHasta AS DATETIME2(0))) END;

    SELECT TOP (@Top)
        p.ProductoID,
        p.Codigo,
        p.Nombre,
        ISNULL(SUM(CASE WHEN m.Tipo = 'ENTRADA' THEN m.Cantidad ELSE 0 END), 0) AS UnidadesEntrada,
        ISNULL(SUM(CASE WHEN m.Tipo = 'SALIDA' THEN m.Cantidad ELSE 0 END), 0) AS UnidadesSalida,
        COUNT(*) AS Movimientos
    FROM dbo.MovimientosInventario AS m
    INNER JOIN dbo.Productos AS p
            ON p.ProductoID = m.ProductoID
    WHERE (@Desde IS NULL OR m.Fecha >= @Desde)
      AND (@Hasta IS NULL OR m.Fecha < @Hasta)
    GROUP BY p.ProductoID, p.Codigo, p.Nombre
    ORDER BY COUNT(*) DESC, p.Nombre;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_Dashboard_UltimosMovimientos
    @Top INT = 8
AS
BEGIN
    SET NOCOUNT ON;

    IF @Top IS NULL OR @Top < 1
        SET @Top = 8;

    IF @Top > 100
        SET @Top = 100;

    SELECT TOP (@Top)
        m.MovimientoID,
        m.Fecha,
        m.Tipo,
        m.Cantidad,
        m.Motivo,
        m.StockAnterior,
        m.StockPosterior,
        p.Codigo AS ProductoCodigo,
        p.Nombre AS ProductoNombre,
        u.NombreUsuario
    FROM dbo.MovimientosInventario AS m
    INNER JOIN dbo.Productos AS p
            ON p.ProductoID = m.ProductoID
    INNER JOIN dbo.Usuarios AS u
            ON u.UsuarioID = m.UsuarioID
    ORDER BY m.Fecha DESC, m.MovimientoID DESC;
END;
GO

PRINT N'04_procedures.sql finalizado: procedimientos almacenados creados o actualizados.';
GO
