"""Esquemas del dashboard."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel


class DashboardResumen(BaseModel):
    productos_activos: int
    productos_inactivos: int
    productos_total: int
    categorias_total: int
    productos_stock_bajo: int
    valor_inventario: float
    unidades_en_stock: int
    movimientos_periodo: int
    unidades_entrada: int
    unidades_salida: int


class MovimientoPorDia(BaseModel):
    fecha: dt.date
    unidades_entrada: int
    unidades_salida: int
    movimientos: int


class TopProducto(BaseModel):
    producto_id: int
    codigo: str
    nombre: str
    unidades_entrada: int
    unidades_salida: int
    movimientos: int


class UltimoMovimiento(BaseModel):
    movimiento_id: int
    fecha: dt.datetime
    tipo: str
    cantidad: int
    motivo: str
    stock_anterior: int
    stock_posterior: int
    producto_codigo: str
    producto_nombre: str
    nombre_usuario: str


class DashboardOut(BaseModel):
    fecha_desde: dt.date
    fecha_hasta: dt.date
    resumen: DashboardResumen
    serie_diaria: list[MovimientoPorDia]
    top_productos: list[TopProducto]
    ultimos_movimientos: list[UltimoMovimiento]
