"""Servicio de productos."""

from __future__ import annotations

from backend.core.errors import AppError, NotFoundError
from backend.repositories.producto_repository import ProductoRepository
from backend.schemas.producto import (
    ProductoCreate,
    ProductoOut,
    ProductoUpdate,
    StockBajoOut,
    ValorInventarioOut,
)


class ProductoService:
    def __init__(self, productos: ProductoRepository) -> None:
        self._productos = productos

    def listar(
        self,
        busqueda: str | None = None,
        categoria_id: int | None = None,
        solo_activos: bool = True,
    ) -> list[ProductoOut]:
        rows = self._productos.listar(busqueda, categoria_id, solo_activos)
        return [self._to_schema(row) for row in rows]

    def obtener(self, producto_id: int) -> ProductoOut:
        row = self._productos.obtener(producto_id)
        if row is None:
            raise NotFoundError("Producto no encontrado.", "producto_no_encontrado")
        return self._to_schema(row)

    def crear(self, data: ProductoCreate) -> ProductoOut:
        producto_id = self._productos.crear(
            codigo=data.codigo,
            nombre=data.nombre,
            descripcion=data.descripcion,
            categoria_id=data.categoria_id,
            precio_compra=data.precio_compra,
            precio_venta=data.precio_venta,
            stock_minimo=data.stock_minimo,
            activo=data.activo,
        )
        return self.obtener(producto_id)

    def actualizar(self, producto_id: int, data: ProductoUpdate) -> ProductoOut:
        self._productos.actualizar(
            producto_id=producto_id,
            codigo=data.codigo,
            nombre=data.nombre,
            descripcion=data.descripcion,
            categoria_id=data.categoria_id,
            precio_compra=data.precio_compra,
            precio_venta=data.precio_venta,
            stock_minimo=data.stock_minimo,
            activo=data.activo,
        )
        return self.obtener(producto_id)

    def desactivar(self, producto_id: int) -> ProductoOut:
        self._productos.desactivar(producto_id)
        return self.obtener(producto_id)

    def activar(self, producto_id: int) -> ProductoOut:
        self._productos.activar(producto_id)
        return self.obtener(producto_id)

    def stock_bajo(self) -> list[StockBajoOut]:
        return [
            StockBajoOut(
                producto_id=row["producto_id"],
                codigo=row["codigo"],
                nombre=row["nombre"],
                categoria_id=row["categoria_id"],
                categoria_nombre=row["categoria_nombre"],
                stock=row["stock"],
                stock_minimo=row["stock_minimo"],
                faltante=row["faltante"],
                precio_compra=row["precio_compra"],
            )
            for row in self._productos.stock_bajo()
        ]

    def valor_inventario(self) -> ValorInventarioOut:
        row = self._productos.valor_inventario()
        if row is None:
            raise AppError(500, "error_interno", "No se pudo calcular el inventario.")
        return ValorInventarioOut(
            valor_inventario=float(row["valor_inventario"]),
            unidades_en_stock=int(row["unidades_en_stock"]),
            productos_con_stock=int(row["productos_con_stock"]),
        )

    @staticmethod
    def _to_schema(row: dict) -> ProductoOut:
        return ProductoOut(
            producto_id=row["producto_id"],
            codigo=row["codigo"],
            nombre=row["nombre"],
            descripcion=row["descripcion"],
            categoria_id=row["categoria_id"],
            categoria_nombre=row["categoria_nombre"],
            precio_compra=row["precio_compra"],
            precio_venta=row["precio_venta"],
            stock=row["stock"],
            stock_minimo=row["stock_minimo"],
            activo=bool(row["activo"]),
            fecha_creacion=row["fecha_creacion"],
            fecha_actualizacion=row["fecha_actualizacion"],
            valor_inventario=row["valor_inventario"],
            stock_bajo=bool(row["stock_bajo"]),
        )
