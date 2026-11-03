"""Hash de contraseñas con Argon2id y emisión/validación de JWT."""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from backend.core.config import Settings
from backend.core.errors import UnauthorizedError

# Parámetros de Argon2id alineados con las recomendaciones de OWASP.
_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
)

# Hash descartable para igualar tiempos cuando el usuario no existe.
_DUMMY_HASH = _hasher.hash("tecnostock-dummy-password")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False
    except Exception:
        return False


def verify_dummy() -> None:
    """Consume tiempo similar a una verificación real (anti-enumeración)."""
    try:
        _hasher.verify(_DUMMY_HASH, "tecnostock-dummy-password")
    except Exception:
        pass


def needs_rehash(password_hash: str) -> bool:
    try:
        return _hasher.check_needs_rehash(password_hash)
    except Exception:
        return False


def create_access_token(
    settings: Settings,
    usuario_id: int,
    nombre_usuario: str,
) -> tuple[str, int]:
    now = dt.datetime.now(dt.UTC)
    expires_delta = dt.timedelta(minutes=settings.access_token_expire_minutes)
    payload: dict[str, Any] = {
        "sub": str(usuario_id),
        "username": nombre_usuario,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "jti": uuid.uuid4().hex,
    }
    token = jwt.encode(
        payload, settings.jwt_secret, algorithm=settings.jwt_algorithm
    )
    return token, int(expires_delta.total_seconds())


def decode_access_token(settings: Settings, token: str) -> dict[str, Any]:
    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "sub"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedError(
            "La sesión expiró. Vuelva a iniciar sesión.", "token_expirado"
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedError("Token inválido.", "token_invalido") from exc
