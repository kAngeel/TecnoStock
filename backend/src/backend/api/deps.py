"""Dependencias compartidas de la API."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.core.config import Settings, get_settings
from backend.core.database import get_pool
from backend.core.errors import UnauthorizedError
from backend.core.security import decode_access_token
from backend.repositories.categoria_repository import CategoriaRepository
from backend.repositories.dashboard_repository import DashboardRepository
from backend.repositories.movimiento_repository import MovimientoRepository
from backend.repositories.producto_repository import ProductoRepository
from backend.repositories.usuario_repository import UsuarioRepository
from backend.schemas.auth import UsuarioOut
from backend.services.auth_service import AuthService
from backend.services.categoria_service import CategoriaService
from backend.services.dashboard_service import DashboardService
from backend.services.movimiento_service import MovimientoService
from backend.services.producto_service import ProductoService

_bearer = HTTPBearer(auto_error=False, description="Token JWT Bearer")


def settings_dep() -> Settings:
    return get_settings()


def usuario_repository() -> UsuarioRepository:
    return UsuarioRepository(get_pool())


def auth_service(
    usuarios: Annotated[UsuarioRepository, Depends(usuario_repository)],
    settings: Annotated[Settings, Depends(settings_dep)],
) -> AuthService:
    return AuthService(usuarios, settings)


def categoria_service() -> CategoriaService:
    return CategoriaService(CategoriaRepository(get_pool()))


def producto_service() -> ProductoService:
    return ProductoService(ProductoRepository(get_pool()))


def movimiento_service() -> MovimientoService:
    return MovimientoService(MovimientoRepository(get_pool()))


def dashboard_service() -> DashboardService:
    return DashboardService(DashboardRepository(get_pool()))


def usuario_actual(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(_bearer)
    ],
    settings: Annotated[Settings, Depends(settings_dep)],
    service: Annotated[AuthService, Depends(auth_service)],
) -> UsuarioOut:
    if credentials is None or not credentials.credentials:
        raise UnauthorizedError(
            "Se requiere autenticación para acceder a este recurso.",
            "token_requerido",
        )

    payload = decode_access_token(settings, credentials.credentials)
    try:
        usuario_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise UnauthorizedError("Token inválido.", "token_invalido") from exc

    return service.obtener_usuario(usuario_id)


UsuarioActual = Annotated[UsuarioOut, Depends(usuario_actual)]
