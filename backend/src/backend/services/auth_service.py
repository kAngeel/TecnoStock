"""Servicio de autenticación."""

from __future__ import annotations

import logging

from backend.core.config import Settings
from backend.core.errors import ForbiddenError, UnauthorizedError
from backend.core.security import (
    create_access_token,
    hash_password,
    needs_rehash,
    verify_dummy,
    verify_password,
)
from backend.repositories.usuario_repository import UsuarioRepository
from backend.schemas.auth import TokenResponse, UsuarioOut

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, usuarios: UsuarioRepository, settings: Settings) -> None:
        self._usuarios = usuarios
        self._settings = settings

    def login(self, nombre_usuario: str, contrasena: str) -> TokenResponse:
        row = self._usuarios.obtener_por_nombre(nombre_usuario)

        if row is None:
            # Mismo costo de cómputo que una verificación real para no
            # revelar si el usuario existe.
            verify_dummy()
            raise UnauthorizedError(
                "Usuario o contraseña incorrectos.", "credenciales_invalidas"
            )

        if not row["activo"]:
            raise ForbiddenError(
                "El usuario está inactivo. Contacte al administrador.",
                "usuario_inactivo",
            )

        if not verify_password(contrasena, row["clave_hash"]):
            raise UnauthorizedError(
                "Usuario o contraseña incorrectos.", "credenciales_invalidas"
            )

        if needs_rehash(row["clave_hash"]):
            self._usuarios.actualizar_hash(
                row["usuario_id"], hash_password(contrasena)
            )

        token, expires_in = create_access_token(
            self._settings, row["usuario_id"], row["nombre_usuario"]
        )

        return TokenResponse(
            access_token=token,
            expires_in=expires_in,
            usuario=UsuarioOut(
                usuario_id=row["usuario_id"],
                nombre_usuario=row["nombre_usuario"],
                nombre_completo=row["nombre_completo"],
                activo=bool(row["activo"]),
                fecha_creacion=row["fecha_creacion"],
            ),
        )

    def obtener_usuario(self, usuario_id: int) -> UsuarioOut:
        row = self._usuarios.obtener_por_id(usuario_id)
        if row is None or not row["activo"]:
            raise UnauthorizedError(
                "La sesión no es válida. Vuelva a iniciar sesión.", "sesion_invalida"
            )
        return UsuarioOut(
            usuario_id=row["usuario_id"],
            nombre_usuario=row["nombre_usuario"],
            nombre_completo=row["nombre_completo"],
            activo=bool(row["activo"]),
            fecha_creacion=row["fecha_creacion"],
        )

    def asegurar_administrador_inicial(self) -> None:
        """Crea el administrador definido en .env si todavía no existe."""
        username = (self._settings.bootstrap_admin_username or "").strip()
        password = self._settings.bootstrap_admin_password or ""

        if not username or not password:
            return

        if len(password) < 8:
            logger.warning(
                "BOOTSTRAP_ADMIN_PASSWORD es demasiado corta (mínimo 8). "
                "No se creó el administrador inicial."
            )
            return

        if self._usuarios.obtener_por_nombre(username) is not None:
            return

        usuario_id = self._usuarios.crear(
            username,
            self._settings.bootstrap_admin_fullname,
            hash_password(password),
        )
        logger.info("Administrador inicial creado (UsuarioID=%s).", usuario_id)
