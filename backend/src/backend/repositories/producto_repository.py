"""Repositorio de productos."""

from __future__ import annotations

from decimal import Decimal

from backend.repositories.base import BaseRepository


class ProductoRepository(BaseRepository):
    def listar(
        self,
        busqueda: str | None = None,
        categoria_id: int | None = None,
        solo_activos: bool = True,
    ) -> list[dict]:
        return self._fetch_all(
            "dbo.usp_Productos_Listar",
            [busqueda, categoria_id, solo_activos],
        )

    def obtener(self, producto_id: int) -> dict | None:
        return self._fetch_one("dbo.usp_Productos_Obtener", [producto_id])

    def crear(
        self,
        codigo: str,
        nombre: str,
        descripcion: str,
        categoria_id: int,
        precio_compra: Decimal,
        precio_venta: Decimal,
        stock_minimo: int,
        activo: bool,
    ) -> int:
        return int(
            self._execute_scalar(
                "DECLARE @id INT; "
                "EXEC dbo.usp_Productos_Insertar ?, ?, ?, ?, ?, ?, ?, ?, @id OUTPUT; "
                "SELECT @id;",
                [
                    codigo,
                    nombre,
                    descripcion,
                    categoria_id,
                    precio_compra,
                    precio_venta,
                    stock_minimo,
                    activo,
                ],
            )
        )

    def actualizar(
        self,
        producto_id: int,
        codigo: str,
        nombre: str,
        descripcion: str,
        categoria_id: int,
        precio_compra: Decimal,
        precio_venta: Decimal,
        stock_minimo: int,
        activo: bool,
    ) -> None:
        self._execute(
            "EXEC dbo.usp_Productos_Actualizar ?, ?, ?, ?, ?, ?, ?, ?, ?",
            [
                producto_id,
                codigo,
                nombre,
                descripcion,
                categoria_id,
                precio_compra,
                precio_venta,
                stock_minimo,
                activo,
            ],
        )

    def desactivar(self, producto_id: int) -> None:
        self._execute("EXEC dbo.usp_Productos_Desactivar ?", [producto_id])

    def activar(self, producto_id: int) -> None:
        self._execute("EXEC dbo.usp_Productos_Activar ?", [producto_id])

    def stock_bajo(self) -> list[dict]:
        return self._fetch_all("dbo.usp_Productos_StockBajo")

    def valor_inventario(self) -> dict | None:
        return self._fetch_one("dbo.usp_Productos_ValorInventario")
