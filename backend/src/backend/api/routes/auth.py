"""Rutas de autenticación."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from backend.api.deps import UsuarioActual, auth_service
from backend.schemas.auth import LoginRequest, TokenResponse, UsuarioOut
from backend.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Iniciar sesión",
)
def login(
    data: LoginRequest,
    service: Annotated[AuthService, Depends(auth_service)],
) -> TokenResponse:
    return service.login(data.nombre_usuario, data.contrasena)


@router.get(
    "/me",
    response_model=UsuarioOut,
    summary="Datos del usuario autenticado",
)
def me(usuario: UsuarioActual) -> UsuarioOut:
    return usuario
