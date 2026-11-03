/*
    TecnoStock - 01_database.sql
    Crea la base de datos TecnoStock si no existe y fija un nivel de
    compatibilidad moderno.

    Por qué se fija la compatibilidad:
      THROW (usado en 02 y 03) requiere nivel de compatibilidad 110 o
      superior. Una base creada hace años o restaurada desde un respaldo
      antiguo puede quedar en 100 y entonces THROW falla con
      "Sintaxis incorrecta cerca de THROW". Este script sube el nivel al
      máximo que soporta el motor instalado y nunca lo baja.

    Es idempotente: puede ejecutarse varias veces sin efectos secundarios.
    No contiene credenciales ni cadenas de conexión.
*/

USE [master];
GO

SET NOCOUNT ON;

IF DB_ID(N'TecnoStock') IS NULL
BEGIN
    CREATE DATABASE [TecnoStock];
    PRINT N'Base de datos TecnoStock creada.';
END
ELSE
BEGIN
    PRINT N'La base de datos TecnoStock ya existe; no se recrea.';
END;
GO

USE [TecnoStock];
GO

SET NOCOUNT ON;

/* Nivel de compatibilidad: major * 10 (2025 -> 170, 2022 -> 160, ...).
   Se usa 110 como mínimo para garantizar THROW. */
DECLARE @major  INT = TRY_CAST(SERVERPROPERTY('ProductMajorVersion') AS INT);
DECLARE @compat INT = CASE WHEN @major >= 11 THEN @major * 10 ELSE 110 END;
DECLARE @actual INT = (SELECT compatibility_level FROM sys.databases WHERE name = DB_NAME());

IF @actual < @compat
BEGIN
    DECLARE @sql NVARCHAR(300) =
        N'ALTER DATABASE ' + QUOTENAME(DB_NAME()) +
        N' SET COMPATIBILITY_LEVEL = ' + CAST(@compat AS NVARCHAR(3)) + N';';
    EXEC sys.sp_executesql @sql;
    PRINT N'Nivel de compatibilidad actualizado de ' + CAST(@actual AS NVARCHAR(3)) +
          N' a ' + CAST(@compat AS NVARCHAR(3)) + N'.';
END
ELSE
BEGIN
    PRINT N'Nivel de compatibilidad ' + CAST(@actual AS NVARCHAR(3)) + N' correcto.';
END;

/* Modelo de recuperación simple: suficiente para desarrollo local y evita
   que el log crezca sin control. */
IF (SELECT recovery_model_desc FROM sys.databases WHERE name = DB_NAME()) <> N'SIMPLE'
BEGIN
    ALTER DATABASE [TecnoStock] SET RECOVERY SIMPLE;
    PRINT N'Modelo de recuperación establecido en SIMPLE.';
END;

PRINT N'Base de datos TecnoStock lista.';
GO
