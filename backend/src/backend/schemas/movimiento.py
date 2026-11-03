"""Esquemas de movimientos de inventario."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MovimientoCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    producto_id: int = Field(gt=0)
    cantidad: int = Field(gt=0, le=1_000_000)
    motivo: str = Field(min_length=1, max_length=200)

    @field_validator("motivo")
    @classmethod
    def _motivo_no_vacio(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El motivo es obligatorio.")
        return value


class MovimientoOut(BaseModel):
    movimiento_id: int
    producto_id: int
    producto_codigo: str
    producto_nombre: str
    usuario_id: int
    nombre_usuario: str
    usuario_nombre_completo: str
    tipo: str
    cantidad: int
    motivo: str
    stock_anterior: int
    stock_posterior: int
    fecha: dt.datetime


class MovimientoRegistrado(BaseModel):
    movimiento_id: int
    producto_id: int
    tipo: str
    cantidad: int
    stock_anterior: int
    stock_posterior: int


class MovimientoPage(BaseModel):
    items: list[MovimientoOut]
    total: int
    pagina: int
    tamano_pagina: int
    total_paginas: int
