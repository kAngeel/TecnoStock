"""Esquemas de categorías."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CategoriaBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nombre: str = Field(min_length=1, max_length=100)
    descripcion: str | None = Field(default=None, max_length=300)

    @field_validator("descripcion")
    @classmethod
    def _blank_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class CategoriaCreate(CategoriaBase):
    pass


class CategoriaUpdate(CategoriaBase):
    pass


class CategoriaOut(BaseModel):
    categoria_id: int
    nombre: str
    descripcion: str | None = None
    total_productos: int = 0
