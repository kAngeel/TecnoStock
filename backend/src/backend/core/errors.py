"""Errores de aplicación y traducción de errores de SQL Server.

Los procedimientos lanzan THROW con códigos 500xx. Aquí se convierten en
respuestas HTTP con un mensaje comprensible para el usuario.
"""

from __future__ import annotations

import re
from typing import Any

import pyodbc


class AppError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details


class NotFoundError(AppError):
    def __init__(self, message: str, code: str = "no_encontrado") -> None:
        super().__init__(404, code, message)


class ConflictError(AppError):
    def __init__(self, message: str, code: str = "conflicto") -> None:
        super().__init__(409, code, message)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Credenciales inválidas.", code: str = "no_autorizado") -> None:
        super().__init__(401, code, message)


class ForbiddenError(AppError):
    def __init__(self, message: str = "No tiene permisos para esta operación.", code: str = "prohibido") -> None:
        super().__init__(403, code, message)


class BusinessError(AppError):
    def __init__(self, message: str, code: str = "regla_negocio") -> None:
        super().__init__(422, code, message)


# Código de error de negocio -> (HTTP, código lógico, mensaje por defecto)
SQL_BUSINESS_ERRORS: dict[int, tuple[int, str]] = {
    50001: (422, "usuario_invalido"),
    50002: (422, "usuario_invalido"),
    50003: (422, "usuario_invalido"),
    50004: (409, "usuario_duplicado"),
    50005: (404, "usuario_no_encontrado"),
    50010: (422, "categoria_invalida"),
    50011: (409, "categoria_duplicada"),
    50012: (404, "categoria_no_encontrada"),
    50020: (422, "producto_invalido"),
    50021: (422, "producto_invalido"),
    50022: (422, "producto_invalido"),
    50023: (422, "producto_invalido"),
    50024: (422, "producto_invalido"),
    50025: (422, "producto_invalido"),
    50026: (422, "categoria_no_encontrada"),
    50027: (409, "producto_duplicado"),
    50028: (404, "producto_no_encontrado"),
    50030: (422, "movimiento_invalido"),
    50031: (422, "movimiento_invalido"),
    50032: (409, "usuario_inactivo"),
    50033: (409, "producto_no_disponible"),
    50034: (409, "stock_insuficiente"),
    50035: (422, "movimiento_invalido"),
}

_BUSINESS_CODE_RE = re.compile(r"\((\d{5})\)")


def _clean_message(raw: str) -> str:
    """Quita el ruido del driver y deja el mensaje de SQL Server."""
    text = raw
    marker = "[SQL Server]"
    if marker in text:
        text = text.split(marker, 1)[1]
    text = text.strip()
    # pyodbc agrega "(SQLExecDirectW)')" al final; el código 500xx se conserva.
    text = re.sub(r"\s*\(SQLExecDirectW\)['\"\)]*\s*$", "", text)
    return text.strip()


def translate_sql_error(exc: Exception) -> AppError:
    """Convierte una excepción de pyodbc en AppError."""
    if isinstance(exc, AppError):
        return exc

    raw = str(exc)
    match = _BUSINESS_CODE_RE.search(raw)

    if match:
        sql_code = int(match.group(1))
        mapped = SQL_BUSINESS_ERRORS.get(sql_code)
        if mapped is not None:
            status, logical_code = mapped
            return AppError(status, logical_code, _clean_message(raw))

    # Errores estándar de SQL Server
    if "[2627]" in raw or "[2601]" in raw:
        return ConflictError(
            "Ya existe un registro con esos datos.", "registro_duplicado"
        )
    if "[547]" in raw:
        return ConflictError(
            "La operación afecta registros relacionados y no está permitida.",
            "restriccion_relacion",
        )
    if "[515]" in raw or "[2628]" in raw:
        return BusinessError(
            "Faltan datos obligatorios o un valor excede la longitud permitida.",
            "datos_invalidos",
        )

    # Conexión / disponibilidad
    if isinstance(exc, (pyodbc.InterfaceError, pyodbc.OperationalError)):
        return AppError(
            503,
            "base_de_datos_no_disponible",
            "No fue posible comunicarse con la base de datos.",
        )

    return AppError(
        500,
        "error_interno",
        "Ocurrió un error inesperado al procesar la solicitud.",
        {"detalle": _clean_message(raw)} if raw else None,
    )
