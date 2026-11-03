/*
    TecnoStock - 05_permissions.sql
    Permisos mínimos para el usuario de la aplicación.

    Modelo:
      - Se crea el rol de base de datos TecnoStockApp.
      - El rol solo puede EJECUTAR procedimientos del esquema dbo.
      - Se deniega SELECT/INSERT/UPDATE/DELETE directos sobre el esquema.
      - Gracias al encadenamiento de propiedad (todas las tablas y
        procedimientos pertenecen a dbo), los procedimientos siguen
        funcionando aunque el usuario no tenga acceso directo a las tablas.

    Esto es lo que garantiza que el stock solo cambie por los procedimientos
    de entrada y salida, y no por un UPDATE directo desde la aplicación.

    El login concreto NO se crea aquí: en desarrollo local se usa
    autenticación de Windows y en producción se crea un login SQL con
    contraseña fuera del repositorio (ver README).
*/

USE [TecnoStock];
GO

SET NOCOUNT ON;

IF DATABASE_PRINCIPAL_ID(N'TecnoStockApp') IS NULL
BEGIN
    CREATE ROLE TecnoStockApp AUTHORIZATION dbo;
    PRINT N'Rol TecnoStockApp creado.';
END
ELSE
BEGIN
    PRINT N'El rol TecnoStockApp ya existe.';
END;
GO

GRANT EXECUTE ON SCHEMA::dbo TO TecnoStockApp;
GO

DENY SELECT, INSERT, UPDATE, DELETE ON SCHEMA::dbo TO TecnoStockApp;
GO

SET NOCOUNT ON;

PRINT N'Permisos aplicados al rol TecnoStockApp: EXECUTE permitido, DML directo denegado.';
PRINT N'';
PRINT N'Para producción, crear un login SQL y agregarlo al rol:';
PRINT N'    CREATE LOGIN [tecnostock_app] WITH PASSWORD = N''<contraseña-fuerte>'';';
PRINT N'    USE [TecnoStock];';
PRINT N'    CREATE USER [tecnostock_app] FOR LOGIN [tecnostock_app];';
PRINT N'    ALTER ROLE [TecnoStockApp] ADD MEMBER [tecnostock_app];';
GO

/* Verificación rápida de los permisos del rol. */
SET NOCOUNT ON;

SELECT
    dp.state_desc AS Estado,
    dp.permission_name AS Permiso,
    dp.class_desc AS Ambito
FROM sys.database_permissions AS dp
WHERE dp.grantee_principal_id = DATABASE_PRINCIPAL_ID(N'TecnoStockApp')
ORDER BY dp.permission_name;
GO
