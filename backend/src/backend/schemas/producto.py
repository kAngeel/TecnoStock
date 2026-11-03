"""Esquemas de productos.

El stock no forma parte de los datos de creación ni de edición: solo cambia
mediante movimientos de inventario.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

PRECIO_MAXIMO = Decimal("9999999999.99")


class ProductoBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    codigo: str = Field(min_length=1, max_length=50)
    nombre: str = Field(min_length=1, max_length=150)
    descripcion: str = Field(min_length=1, max_length=500)
    categoria_id: int = Field(gt=0)
    precio_compra: Decimal = Field(gt=0, le=PRECIO_MAXIMO, decimal_places=2)
    precio_venta: Decimal = Field(gt=0, le=PRECIO_MAXIMO, decimal_places=2)
    stock_minimo: int = Field(ge=0, le=1_000_000)

    @field_validator("precio_compra", "precio_venta")
    @classmethod
    def _dos_decimales(cls, value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"))

    @field_validator("descripcion")
    @classmethod
    def _descripcion_no_vacia(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("La descripción es obligatoria.")
        return value


class ProductoCreate(ProductoBase):
    activo: bool = True


class ProductoUpdate(ProductoBase):
    activo: bool = True


class ProductoOut(BaseModel):
    producto_id: int
    codigo: str
    nombre: str
    descripcion: str
    categoria_id: int
    categoria_nombre: str
    precio_compra: float
    precio_venta: float
    stock: int
    stock_minimo: int
    activo: bool
    fecha_creacion: dt.datetime
    fecha_actualizacion: dt.datetime
    valor_inventario: float
    stock_bajo: bool


class StockBajoOut(BaseModel):
    producto_id: int
    codigo: str
    nombre: str
    categoria_id: int
    categoria_nombre: str
    stock: int
    stock_minimo: int
    faltante: int
    precio_compra: float
