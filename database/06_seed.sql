/*
    TecnoStock - 06_seed.sql
    Datos iniciales mínimos.

    Solo categorías por defecto, con inserción idempotente (no duplica).
    El usuario administrador NO se crea aquí porque su contraseña debe
    almacenarse como hash Argon2id, y ese hash lo genera el backend al
    arrancar (ver backend/.env.example: BOOTSTRAP_ADMIN_*).
*/

USE [TecnoStock];
GO

SET NOCOUNT ON;

IF NOT EXISTS (SELECT 1 FROM dbo.Categorias WHERE Nombre = N'Computadoras')
    INSERT INTO dbo.Categorias (Nombre, Descripcion)
    VALUES (N'Computadoras', N'Equipos de escritorio, portátiles y todo en uno.');

IF NOT EXISTS (SELECT 1 FROM dbo.Categorias WHERE Nombre = N'Componentes')
    INSERT INTO dbo.Categorias (Nombre, Descripcion)
    VALUES (N'Componentes', N'Procesadores, memorias, discos y tarjetas.');

IF NOT EXISTS (SELECT 1 FROM dbo.Categorias WHERE Nombre = N'Periféricos')
    INSERT INTO dbo.Categorias (Nombre, Descripcion)
    VALUES (N'Periféricos', N'Teclados, mouse, monitores e impresoras.');

IF NOT EXISTS (SELECT 1 FROM dbo.Categorias WHERE Nombre = N'Redes')
    INSERT INTO dbo.Categorias (Nombre, Descripcion)
    VALUES (N'Redes', N'Routers, switches, cableado y accesorios de red.');

IF NOT EXISTS (SELECT 1 FROM dbo.Categorias WHERE Nombre = N'Almacenamiento')
    INSERT INTO dbo.Categorias (Nombre, Descripcion)
    VALUES (N'Almacenamiento', N'Discos SSD, HDD y unidades externas.');

SELECT CategoriaID, Nombre FROM dbo.Categorias ORDER BY Nombre;
GO
