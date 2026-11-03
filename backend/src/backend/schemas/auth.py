"""Esquemas de autenticación."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nombre_usuario: str = Field(min_length=1, max_length=50)
    contrasena: str = Field(min_length=8, max_length=128)


class UsuarioOut(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    usuario_id: int
    nombre_usuario: str
    nombre_completo: str
    activo: bool
    fecha_creacion: dt.datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    usuario: UsuarioOut
