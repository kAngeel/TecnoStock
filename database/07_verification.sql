/*
    TecnoStock - 07_verification.sql
    Script de VERIFICACIÓN. Solo lectura: no crea, altera ni elimina objetos
    ni datos.

    Ejecutar después de:
        01_database.sql
        02_tables.sql
        03_constraints_indexes.sql

    Uso:
        sqlcmd -S .\SQLEXPRESS -E -i 07_verification.sql
    o abrir en SSMS y ejecutar el archivo completo.

    El script es un único lote (no usa GO) para poder abortar limpiamente si
    la base no existe. Requiere SQL Server 2012 o superior.
*/

SET NOCOUNT ON;
SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;

IF DB_ID(N'TecnoStock') IS NULL
BEGIN
    PRINT N'[ERROR] La base TecnoStock no existe.';
    PRINT N'Ejecute 01_database.sql, 02_tables.sql y 03_constraints_indexes.sql antes de verificar.';
    RETURN;
END;

/* ============================================================
   1. Tablas esperadas
   ============================================================ */

PRINT N'';
PRINT N'=== 1. TABLAS ===';

SELECT
    v.Tabla,
    CASE WHEN OBJECT_ID(N'TecnoStock.dbo.' + v.Tabla, N'U') IS NULL
         THEN N'FALTA'
         ELSE N'OK'
    END AS Estado,
    CAST(t.create_date AS DATETIME2(0)) AS Creada
FROM (VALUES
        (N'Categorias'),
        (N'Usuarios'),
        (N'Productos'),
        (N'MovimientosInventario')
     ) AS v (Tabla)
LEFT JOIN TecnoStock.sys.tables AS t
       ON t.object_id = OBJECT_ID(N'TecnoStock.dbo.' + v.Tabla, N'U')
ORDER BY v.Tabla;

/* ============================================================
   2. Columnas por tabla y número de columnas
   ============================================================ */

PRINT N'';
PRINT N'=== 2. COLUMNAS ===';

SELECT
    t.name AS Tabla,
    c.column_id AS Orden,
    c.name AS Columna,
    ty.name AS Tipo,
    CASE
        WHEN c.max_length = -1 THEN N'MAX'
        WHEN ty.name IN (N'nvarchar', N'nchar') THEN CAST(c.max_length / 2 AS VARCHAR(10))
        ELSE CAST(c.max_length AS VARCHAR(10))
    END AS Longitud,
    c.precision AS Precision,
    c.scale AS Escala,
    CASE c.is_nullable WHEN 1 THEN N'NULL' ELSE N'NOT NULL' END AS Nulabilidad,
    CASE c.is_identity WHEN 1 THEN N'IDENTITY' ELSE N'' END AS Identidad,
    dc.name AS RestriccionDefault,
    dc.definition AS DefinicionDefault
FROM TecnoStock.sys.tables AS t
JOIN TecnoStock.sys.columns AS c
  ON c.object_id = t.object_id
JOIN TecnoStock.sys.types AS ty
  ON ty.user_type_id = c.user_type_id
LEFT JOIN TecnoStock.sys.default_constraints AS dc
  ON dc.parent_object_id = t.object_id
 AND dc.parent_column_id = c.column_id
WHERE t.object_id IN
      (
          OBJECT_ID(N'TecnoStock.dbo.Categorias', N'U'),
          OBJECT_ID(N'TecnoStock.dbo.Usuarios', N'U'),
          OBJECT_ID(N'TecnoStock.dbo.Productos', N'U'),
          OBJECT_ID(N'TecnoStock.dbo.MovimientosInventario', N'U')
      )
ORDER BY t.name, c.column_id;

PRINT N'';
SELECT
    t.name AS Tabla,
    COUNT(*) AS Columnas,
    CASE t.name
        WHEN N'Categorias' THEN 3
        WHEN N'Usuarios' THEN 6
        WHEN N'Productos' THEN 12
        WHEN N'MovimientosInventario' THEN 9
    END AS ColumnasEsperadas,
    CASE WHEN COUNT(*) =
              CASE t.name
                  WHEN N'Categorias' THEN 3
                  WHEN N'Usuarios' THEN 6
                  WHEN N'Productos' THEN 12
                  WHEN N'MovimientosInventario' THEN 9
              END
         THEN N'OK'
         ELSE N'REVISAR'
    END AS Estado
FROM TecnoStock.sys.tables AS t
JOIN TecnoStock.sys.columns AS c
  ON c.object_id = t.object_id
WHERE t.object_id IN
      (
          OBJECT_ID(N'TecnoStock.dbo.Categorias', N'U'),
          OBJECT_ID(N'TecnoStock.dbo.Usuarios', N'U'),
          OBJECT_ID(N'TecnoStock.dbo.Productos', N'U'),
          OBJECT_ID(N'TecnoStock.dbo.MovimientosInventario', N'U')
      )
GROUP BY t.name
ORDER BY t.name;

/* ============================================================
   3. Claves primarias y restricciones UNIQUE
   ============================================================ */

PRINT N'';
PRINT N'=== 3. CLAVES PRIMARIAS Y UNIQUE ===';

SELECT
    t.name AS Tabla,
    kc.name AS Restriccion,
    CASE kc.type WHEN N'PK' THEN N'PRIMARY KEY' ELSE N'UNIQUE' END AS Tipo,
    i.type_desc AS TipoIndice,
    ic.key_ordinal AS Orden,
    c.name AS Columna
FROM TecnoStock.sys.key_constraints AS kc
JOIN TecnoStock.sys.tables AS t
  ON t.object_id = kc.parent_object_id
JOIN TecnoStock.sys.indexes AS i
  ON i.object_id = kc.parent_object_id
 AND i.index_id = kc.unique_index_id
JOIN TecnoStock.sys.index_columns AS ic
  ON ic.object_id = i.object_id
 AND ic.index_id = i.index_id
 AND ic.is_included_column = 0
JOIN TecnoStock.sys.columns AS c
  ON c.object_id = ic.object_id
 AND c.column_id = ic.column_id
WHERE t.object_id IN
      (
          OBJECT_ID(N'TecnoStock.dbo.Categorias', N'U'),
          OBJECT_ID(N'TecnoStock.dbo.Usuarios', N'U'),
          OBJECT_ID(N'TecnoStock.dbo.Productos', N'U'),
          OBJECT_ID(N'TecnoStock.dbo.MovimientosInventario', N'U')
      )
ORDER BY t.name, kc.type DESC, kc.name, ic.key_ordinal;

/* ============================================================
   4. Claves foráneas
   ============================================================ */

PRINT N'';
PRINT N'=== 4. CLAVES FORÁNEAS ===';

SELECT
    fk.name AS Restriccion,
    tp.name AS TablaHija,
    cp.name AS ColumnaHija,
    tr.name AS TablaPadre,
    cr.name AS ColumnaPadre,
    fk.delete_referential_action_desc AS OnDelete,
    fk.update_referential_action_desc AS OnUpdate,
    CASE WHEN fk.is_disabled = 1 THEN N'SI' ELSE N'NO' END AS Deshabilitada,
    CASE WHEN fk.is_not_trusted = 1 THEN N'SI' ELSE N'NO' END AS NoConfiable,
    CASE WHEN fk.is_not_for_replication = 1 THEN N'SI' ELSE N'NO' END AS NoReplicacion
FROM TecnoStock.sys.foreign_keys AS fk
JOIN TecnoStock.sys.foreign_key_columns AS fkc
  ON fkc.constraint_object_id = fk.object_id
JOIN TecnoStock.sys.tables AS tp
  ON tp.object_id = fk.parent_object_id
JOIN TecnoStock.sys.columns AS cp
  ON cp.object_id = fkc.parent_object_id
 AND cp.column_id = fkc.parent_column_id
JOIN TecnoStock.sys.tables AS tr
  ON tr.object_id = fk.referenced_object_id
JOIN TecnoStock.sys.columns AS cr
  ON cr.object_id = fkc.referenced_object_id
 AND cr.column_id = fkc.referenced_column_id
WHERE tr.object_id IN
      (
          OBJECT_ID(N'TecnoStock.dbo.Categorias', N'U'),
          OBJECT_ID(N'TecnoStock.dbo.Usuarios', N'U'),
          OBJECT_ID(N'TecnoStock.dbo.Productos', N'U'),
          OBJECT_ID(N'TecnoStock.dbo.MovimientosInventario', N'U')
      )
ORDER BY fk.name;

/* ============================================================
   5. Restricciones CHECK
   ============================================================ */

PRINT N'';
PRINT N'=== 5. RESTRICCIONES CHECK ===';

SELECT
    t.name AS Tabla,
    cc.name AS Restriccion,
    cc.definition AS Definicion,
    CASE WHEN cc.is_disabled = 1 THEN N'SI' ELSE N'NO' END AS Deshabilitada,
    CASE WHEN cc.is_not_trusted = 1 THEN N'SI' ELSE N'NO' END AS NoConfiable
FROM TecnoStock.sys.check_constraints AS cc
JOIN TecnoStock.sys.tables AS t
  ON t.object_id = cc.parent_object_id
WHERE cc.parent_object_id IN
      (
          OBJECT_ID(N'TecnoStock.dbo.Categorias', N'U'),
          OBJECT_ID(N'TecnoStock.dbo.Usuarios', N'U'),
          OBJECT_ID(N'TecnoStock.dbo.Productos', N'U'),
          OBJECT_ID(N'TecnoStock.dbo.MovimientosInventario', N'U')
      )
ORDER BY t.name, cc.name;

/* ============================================================
   6. Índices
   ============================================================ */

PRINT N'';
PRINT N'=== 6. ÍNDICES ===';

SELECT
    t.name AS Tabla,
    i.name AS Indice,
    i.type_desc AS TipoIndice,
    CASE WHEN i.is_unique = 1 THEN N'SI' ELSE N'NO' END AS Unico,
    ic.key_ordinal AS Orden,
    c.name AS Columna,
    CASE
        WHEN ic.is_included_column = 1 THEN N'INCLUDE'
        WHEN ic.is_descending_key = 1 THEN N'DESC'
        ELSE N'ASC'
    END AS Rol
FROM TecnoStock.sys.indexes AS i
JOIN TecnoStock.sys.tables AS t
  ON t.object_id = i.object_id
JOIN TecnoStock.sys.index_columns AS ic
  ON ic.object_id = i.object_id
 AND ic.index_id = i.index_id
JOIN TecnoStock.sys.columns AS c
  ON c.object_id = ic.object_id
 AND c.column_id = ic.column_id
WHERE i.name IS NOT NULL
  AND i.type > 0
  AND t.object_id IN
      (
          OBJECT_ID(N'TecnoStock.dbo.Categorias', N'U'),
          OBJECT_ID(N'TecnoStock.dbo.Usuarios', N'U'),
          OBJECT_ID(N'TecnoStock.dbo.Productos', N'U'),
          OBJECT_ID(N'TecnoStock.dbo.MovimientosInventario', N'U')
      )
ORDER BY t.name, i.name, ic.key_ordinal, ic.index_column_id;

/* ============================================================
   7. Inventario de objetos esperados vs. reales
      Detecta objetos faltantes y objetos no previstos.
   ============================================================ */

PRINT N'';
PRINT N'=== 7. OBJETOS ESPERADOS FALTANTES O NO PREVISTOS ===';

DECLARE @esperados TABLE
(
    Tipo   VARCHAR(3) NOT NULL,
    Nombre SYSNAME NOT NULL,
    PRIMARY KEY (Tipo, Nombre)
);

INSERT INTO @esperados (Tipo, Nombre)
VALUES
    ('TAB', N'Categorias'),
    ('TAB', N'Usuarios'),
    ('TAB', N'Productos'),
    ('TAB', N'MovimientosInventario'),

    ('PK', N'PK_Categorias'),
    ('PK', N'PK_Usuarios'),
    ('PK', N'PK_Productos'),
    ('PK', N'PK_MovimientosInventario'),

    ('UQ', N'UQ_Categorias_Nombre'),
    ('UQ', N'UQ_Usuarios_NombreUsuario'),
    ('UQ', N'UQ_Productos_Codigo'),

    ('FK', N'FK_Productos_Categorias'),
    ('FK', N'FK_MovimientosInventario_Productos'),
    ('FK', N'FK_MovimientosInventario_Usuarios'),

    ('CK', N'CK_Categorias_Nombre_NoVacio'),
    ('CK', N'CK_Productos_Codigo_NoVacio'),
    ('CK', N'CK_Productos_Nombre_NoVacio'),
    ('CK', N'CK_Productos_Descripcion_NoVacia'),
    ('CK', N'CK_Productos_PrecioCompra_Positivo'),
    ('CK', N'CK_Productos_PrecioVenta_Positivo'),
    ('CK', N'CK_Productos_Stock_NoNegativo'),
    ('CK', N'CK_Productos_StockMinimo_NoNegativo'),
    ('CK', N'CK_Usuarios_NombreUsuario_NoVacio'),
    ('CK', N'CK_Usuarios_NombreCompleto_NoVacio'),
    ('CK', N'CK_Usuarios_ClaveHash_NoVacia'),
    ('CK', N'CK_MovimientosInventario_Tipo_Valido'),
    ('CK', N'CK_MovimientosInventario_Cantidad_Positiva'),
    ('CK', N'CK_MovimientosInventario_Motivo_NoVacio'),
    ('CK', N'CK_MovimientosInventario_Stock_NoNegativo'),
    ('CK', N'CK_MovimientosInventario_Stock_Consistente'),

    ('DF', N'DF_Usuarios_Activo'),
    ('DF', N'DF_Usuarios_FechaCreacion'),
    ('DF', N'DF_Productos_Stock'),
    ('DF', N'DF_Productos_StockMinimo'),
    ('DF', N'DF_Productos_Activo'),
    ('DF', N'DF_Productos_FechaCreacion'),
    ('DF', N'DF_Productos_FechaActualizacion'),
    ('DF', N'DF_MovimientosInventario_Fecha'),

    ('IX', N'IX_Productos_CategoriaID'),
    ('IX', N'IX_Productos_Activo_Stock'),
    ('IX', N'IX_MovimientosInventario_Producto_Fecha'),
    ('IX', N'IX_MovimientosInventario_Fecha'),
    ('IX', N'IX_MovimientosInventario_UsuarioID');

DECLARE @reales TABLE
(
    Tipo   VARCHAR(3) NOT NULL,
    Nombre SYSNAME NOT NULL,
    PRIMARY KEY (Tipo, Nombre)
);

INSERT INTO @reales (Tipo, Nombre)
SELECT 'TAB', t.name
FROM TecnoStock.sys.tables AS t
WHERE t.object_id IN
      (
          OBJECT_ID(N'TecnoStock.dbo.Categorias', N'U'),
          OBJECT_ID(N'TecnoStock.dbo.Usuarios', N'U'),
          OBJECT_ID(N'TecnoStock.dbo.Productos', N'U'),
          OBJECT_ID(N'TecnoStock.dbo.MovimientosInventario', N'U')
      )
UNION
SELECT CASE kc.type WHEN 'PK' THEN 'PK' ELSE 'UQ' END, kc.name
FROM TecnoStock.sys.key_constraints AS kc
WHERE kc.parent_object_id IN
      (
          OBJECT_ID(N'TecnoStock.dbo.Categorias', N'U'),
          OBJECT_ID(N'TecnoStock.dbo.Usuarios', N'U'),
          OBJECT_ID(N'TecnoStock.dbo.Productos', N'U'),
          OBJECT_ID(N'TecnoStock.dbo.MovimientosInventario', N'U')
      )
UNION
SELECT 'FK', fk.name
FROM TecnoStock.sys.foreign_keys AS fk
WHERE fk.referenced_object_id IN
      (
          OBJECT_ID(N'TecnoStock.dbo.Categorias', N'U'),
          OBJECT_ID(N'TecnoStock.dbo.Usuarios', N'U'),
          OBJECT_ID(N'TecnoStock.dbo.Productos', N'U'),
          OBJECT_ID(N'TecnoStock.dbo.MovimientosInventario', N'U')
      )
UNION
SELECT 'CK', cc.name
FROM TecnoStock.sys.check_constraints AS cc
WHERE cc.parent_object_id IN
      (
          OBJECT_ID(N'TecnoStock.dbo.Categorias', N'U'),
          OBJECT_ID(N'TecnoStock.dbo.Usuarios', N'U'),
          OBJECT_ID(N'TecnoStock.dbo.Productos', N'U'),
          OBJECT_ID(N'TecnoStock.dbo.MovimientosInventario', N'U')
      )
UNION
SELECT 'DF', dc.name
FROM TecnoStock.sys.default_constraints AS dc
WHERE dc.parent_object_id IN
      (
          OBJECT_ID(N'TecnoStock.dbo.Categorias', N'U'),
          OBJECT_ID(N'TecnoStock.dbo.Usuarios', N'U'),
          OBJECT_ID(N'TecnoStock.dbo.Productos', N'U'),
          OBJECT_ID(N'TecnoStock.dbo.MovimientosInventario', N'U')
      )
UNION
SELECT 'IX', i.name
FROM TecnoStock.sys.indexes AS i
WHERE i.name IS NOT NULL
  AND i.is_primary_key = 0
  AND i.is_unique_constraint = 0
  AND i.object_id IN
      (
          OBJECT_ID(N'TecnoStock.dbo.Categorias', N'U'),
          OBJECT_ID(N'TecnoStock.dbo.Usuarios', N'U'),
          OBJECT_ID(N'TecnoStock.dbo.Productos', N'U'),
          OBJECT_ID(N'TecnoStock.dbo.MovimientosInventario', N'U')
      );

SELECT Resultado.Resultado, Resultado.Tipo, Resultado.Nombre
FROM
(
    SELECT N'FALTA' AS Resultado, e.Tipo, e.Nombre
    FROM @esperados AS e
    LEFT JOIN @reales AS r
           ON r.Tipo = e.Tipo
          AND r.Nombre = e.Nombre
    WHERE r.Nombre IS NULL

    UNION ALL

    SELECT N'NO PREVISTO' AS Resultado, r.Tipo, r.Nombre
    FROM @reales AS r
    LEFT JOIN @esperados AS e
           ON e.Tipo = r.Tipo
          AND e.Nombre = r.Nombre
    WHERE e.Nombre IS NULL
) AS Resultado
ORDER BY Resultado.Resultado, Resultado.Tipo, Resultado.Nombre;

/* ============================================================
   8. Conteo de filas
   ============================================================ */

PRINT N'';
PRINT N'=== 8. FILAS POR TABLA ===';

IF OBJECT_ID(N'TecnoStock.dbo.Categorias', N'U') IS NOT NULL
   AND OBJECT_ID(N'TecnoStock.dbo.Usuarios', N'U') IS NOT NULL
   AND OBJECT_ID(N'TecnoStock.dbo.Productos', N'U') IS NOT NULL
   AND OBJECT_ID(N'TecnoStock.dbo.MovimientosInventario', N'U') IS NOT NULL
BEGIN
    SELECT N'Categorias' AS Tabla, COUNT_BIG(*) AS Filas FROM TecnoStock.dbo.Categorias
    UNION ALL
    SELECT N'Usuarios', COUNT_BIG(*) FROM TecnoStock.dbo.Usuarios
    UNION ALL
    SELECT N'Productos', COUNT_BIG(*) FROM TecnoStock.dbo.Productos
    UNION ALL
    SELECT N'MovimientosInventario', COUNT_BIG(*) FROM TecnoStock.dbo.MovimientosInventario;
END
ELSE
BEGIN
    PRINT N'[OMITIDO] Faltan tablas; no se puede contar filas.';
END;

/* ============================================================
   9. Integridad de datos
      Todas las comprobaciones deben devolver 0.
   ============================================================ */

PRINT N'';
PRINT N'=== 9. INTEGRIDAD DE DATOS ===';

IF OBJECT_ID(N'TecnoStock.dbo.Categorias', N'U') IS NOT NULL
   AND OBJECT_ID(N'TecnoStock.dbo.Usuarios', N'U') IS NOT NULL
   AND OBJECT_ID(N'TecnoStock.dbo.Productos', N'U') IS NOT NULL
   AND OBJECT_ID(N'TecnoStock.dbo.MovimientosInventario', N'U') IS NOT NULL
BEGIN
    DECLARE @integridad TABLE
    (
        Comprobacion NVARCHAR(200) NOT NULL,
        Hallazgos    INT NOT NULL
    );

    INSERT INTO @integridad (Comprobacion, Hallazgos)
    SELECT N'Productos con Stock negativo',
           COUNT(*)
    FROM TecnoStock.dbo.Productos
    WHERE Stock < 0

    UNION ALL

    SELECT N'Productos con StockMinimo negativo',
           COUNT(*)
    FROM TecnoStock.dbo.Productos
    WHERE StockMinimo < 0

    UNION ALL

    SELECT N'Productos con PrecioCompra o PrecioVenta <= 0',
           COUNT(*)
    FROM TecnoStock.dbo.Productos
    WHERE PrecioCompra <= 0 OR PrecioVenta <= 0

    UNION ALL

    SELECT N'Productos sin categoría existente',
           COUNT(*)
    FROM TecnoStock.dbo.Productos AS p
    WHERE NOT EXISTS
          (
              SELECT 1
              FROM TecnoStock.dbo.Categorias AS c
              WHERE c.CategoriaID = p.CategoriaID
          )

    UNION ALL

    SELECT N'Movimientos con tipo distinto de ENTRADA/SALIDA',
           COUNT(*)
    FROM TecnoStock.dbo.MovimientosInventario
    WHERE Tipo NOT IN ('ENTRADA', 'SALIDA')

    UNION ALL

    SELECT N'Movimientos con Cantidad <= 0',
           COUNT(*)
    FROM TecnoStock.dbo.MovimientosInventario
    WHERE Cantidad <= 0

    UNION ALL

    SELECT N'Movimientos con stock anterior o posterior negativo',
           COUNT(*)
    FROM TecnoStock.dbo.MovimientosInventario
    WHERE StockAnterior < 0 OR StockPosterior < 0

    UNION ALL

    SELECT N'Movimientos con aritmética inconsistente',
           COUNT(*)
    FROM TecnoStock.dbo.MovimientosInventario
    WHERE NOT
          (
              (Tipo = 'ENTRADA' AND StockPosterior = StockAnterior + Cantidad)
              OR
              (Tipo = 'SALIDA' AND StockPosterior = StockAnterior - Cantidad)
          )

    UNION ALL

    SELECT N'Salidas que superan el stock anterior',
           COUNT(*)
    FROM TecnoStock.dbo.MovimientosInventario
    WHERE Tipo = 'SALIDA' AND Cantidad > StockAnterior

    UNION ALL

    SELECT N'Movimientos sin producto existente',
           COUNT(*)
    FROM TecnoStock.dbo.MovimientosInventario AS m
    WHERE NOT EXISTS
          (
              SELECT 1
              FROM TecnoStock.dbo.Productos AS p
              WHERE p.ProductoID = m.ProductoID
          )

    UNION ALL

    SELECT N'Movimientos sin usuario existente',
           COUNT(*)
    FROM TecnoStock.dbo.MovimientosInventario AS m
    WHERE NOT EXISTS
          (
              SELECT 1
              FROM TecnoStock.dbo.Usuarios AS u
              WHERE u.UsuarioID = m.UsuarioID
          )

    UNION ALL

    SELECT N'Productos con Stock distinto del último movimiento',
           COUNT(*)
    FROM TecnoStock.dbo.Productos AS p
    CROSS APPLY
    (
        SELECT TOP (1) m.StockPosterior
        FROM TecnoStock.dbo.MovimientosInventario AS m
        WHERE m.ProductoID = p.ProductoID
        ORDER BY m.Fecha DESC, m.MovimientoID DESC
    ) AS ultimo
    WHERE p.Stock <> ultimo.StockPosterior

    UNION ALL

    SELECT N'Productos con Stock distinto de 0 y sin movimientos',
           COUNT(*)
    FROM TecnoStock.dbo.Productos AS p
    WHERE p.Stock <> 0
      AND NOT EXISTS
          (
              SELECT 1
              FROM TecnoStock.dbo.MovimientosInventario AS m
              WHERE m.ProductoID = p.ProductoID
          );

    SELECT
        Comprobacion,
        Hallazgos,
        CASE WHEN Hallazgos = 0 THEN N'OK' ELSE N'REVISAR' END AS Estado
    FROM @integridad
    ORDER BY CASE WHEN Hallazgos = 0 THEN 1 ELSE 0 END, Comprobacion;

    DECLARE @totalHallazgos INT = (SELECT ISNULL(SUM(Hallazgos), 0) FROM @integridad);

    PRINT N'';
    IF @totalHallazgos = 0
        PRINT N'=== RESULTADO GLOBAL: OK (0 hallazgos de datos) ===';
    ELSE
        PRINT N'=== RESULTADO GLOBAL: REVISAR (' + CAST(@totalHallazgos AS VARCHAR(20)) + N' hallazgos de datos) ===';
END
ELSE
BEGIN
    PRINT N'[OMITIDO] Faltan tablas; no se puede comprobar la integridad de datos.';
END;

/* ============================================================
   10. Estado de confianza de las restricciones
   ============================================================ */

PRINT N'';
PRINT N'=== 10. RESTRICCIONES DESHABILITADAS O NO CONFIABLES ===';

SELECT
    N'FK deshabilitadas' AS Comprobacion,
    COUNT(*) AS Hallazgos
FROM TecnoStock.sys.foreign_keys
WHERE is_disabled = 1

UNION ALL

SELECT N'FK no confiables', COUNT(*)
FROM TecnoStock.sys.foreign_keys
WHERE is_not_trusted = 1

UNION ALL

SELECT N'CHECK deshabilitadas', COUNT(*)
FROM TecnoStock.sys.check_constraints
WHERE is_disabled = 1

UNION ALL

SELECT N'CHECK no confiables', COUNT(*)
FROM TecnoStock.sys.check_constraints
WHERE is_not_trusted = 1;

/* ============================================================
   11. Procedimientos almacenados esperados
   ============================================================ */

PRINT N'';
PRINT N'=== 11. PROCEDIMIENTOS ALMACENADOS ===';

SELECT
    e.Nombre AS Procedimiento,
    CASE WHEN p.object_id IS NULL THEN N'FALTA' ELSE N'OK' END AS Estado,
    CAST(p.modify_date AS DATETIME2(0)) AS UltimaModificacion
FROM (VALUES
        (N'usp_Usuarios_ObtenerPorNombreUsuario'),
        (N'usp_Usuarios_ObtenerPorID'),
        (N'usp_Usuarios_Insertar'),
        (N'usp_Usuarios_Listar'),
        (N'usp_Usuarios_ActualizarClaveHash'),
        (N'usp_Categorias_Listar'),
        (N'usp_Categorias_Obtener'),
        (N'usp_Categorias_Insertar'),
        (N'usp_Categorias_Actualizar'),
        (N'usp_Productos_Listar'),
        (N'usp_Productos_Obtener'),
        (N'usp_Productos_Insertar'),
        (N'usp_Productos_Actualizar'),
        (N'usp_Productos_Desactivar'),
        (N'usp_Productos_Activar'),
        (N'usp_Productos_StockBajo'),
        (N'usp_Productos_ValorInventario'),
        (N'usp_MovimientosInventario_RegistrarEntrada'),
        (N'usp_MovimientosInventario_RegistrarSalida'),
        (N'usp_MovimientosInventario_Listar'),
        (N'usp_Dashboard_Resumen'),
        (N'usp_Dashboard_MovimientosPorDia'),
        (N'usp_Dashboard_TopProductos'),
        (N'usp_Dashboard_UltimosMovimientos')
     ) AS e (Nombre)
LEFT JOIN TecnoStock.sys.procedures AS p
       ON p.name = e.Nombre
      AND p.schema_id = (SELECT schema_id FROM TecnoStock.sys.schemas WHERE name = N'dbo')
ORDER BY e.Nombre;

/* ============================================================
   12. Rol de aplicación y permisos mínimos
   ============================================================ */

PRINT N'';
PRINT N'=== 12. ROL Y PERMISOS ===';

SELECT
    N'Rol TecnoStockApp' AS Comprobacion,
    CASE WHEN EXISTS
              (
                  SELECT 1
                  FROM TecnoStock.sys.database_principals AS pr
                  WHERE pr.name = N'TecnoStockApp'
                    AND pr.type = 'R'
              )
         THEN N'OK' ELSE N'FALTA' END AS Estado

UNION ALL

SELECT
    N'EXECUTE sobre esquema dbo',
    CASE WHEN EXISTS
              (
                  SELECT 1
                  FROM TecnoStock.sys.database_permissions AS dp
                  JOIN TecnoStock.sys.database_principals AS pr
                    ON pr.principal_id = dp.grantee_principal_id
                  WHERE pr.name = N'TecnoStockApp'
                    AND dp.permission_name = N'EXECUTE'
                    AND dp.state = N'G'
              )
         THEN N'OK' ELSE N'FALTA' END

UNION ALL

SELECT
    N'DML directo denegado',
    CASE WHEN
              (
                  SELECT COUNT(*)
                  FROM TecnoStock.sys.database_permissions AS dp
                  JOIN TecnoStock.sys.database_principals AS pr
                    ON pr.principal_id = dp.grantee_principal_id
                  WHERE pr.name = N'TecnoStockApp'
                    AND dp.permission_name IN (N'SELECT', N'INSERT', N'UPDATE', N'DELETE')
                    AND dp.state = N'D'
              ) = 4
         THEN N'OK' ELSE N'REVISAR' END;

PRINT N'';
PRINT N'Verificación finalizada. Este script no modificó la base de datos.';
