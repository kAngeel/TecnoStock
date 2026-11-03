"""Utilidades comunes de acceso a datos con pyodbc.

Todas las operaciones se ejecutan con EXEC sobre procedimientos almacenados.
Ningún repositorio arma INSERT/UPDATE/DELETE directos.

Los errores de SQL Server (incluidos los THROW de negocio 500xx) se traducen
aquí a AppError para que la capa HTTP responda con el código correcto y no
como un error interno genérico.
"""

from __future__ import annotations

import re

import pyodbc

from backend.core.database import ConnectionPool
from backend.core.errors import AppError, translate_sql_error


def to_snake_case(name: str) -> str:
    """Convierte un alias SQL (PascalCase) a clave de diccionario.

    ProductoID -> producto_id, StockBajo -> stock_bajo,
    UnidadesEntrada -> unidades_entrada.
    """
    step1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", step1).lower()


def _row_to_dict(cursor_description, row) -> dict:
    columns = [to_snake_case(column[0]) for column in cursor_description]
    return dict(zip(columns, row, strict=True))


class BaseRepository:
    def __init__(self, pool: ConnectionPool) -> None:
        self._pool = pool

    # ------------------------------------------------------------------
    def _fetch_all(self, procedure: str, params: list | None = None) -> list[dict]:
        params = params or []
        try:
            with self._pool.connection() as connection:
                cursor = connection.cursor()
                if params:
                    placeholders = ", ".join("?" for _ in params)
                    cursor.execute(f"EXEC {procedure} {placeholders}", params)
                else:
                    cursor.execute(f"EXEC {procedure}")
                if cursor.description is None:
                    return []
                return [
                    _row_to_dict(cursor.description, row) for row in cursor.fetchall()
                ]
        except pyodbc.Error as exc:
            raise translate_sql_error(exc) from exc

    def _fetch_one(self, procedure: str, params: list | None = None) -> dict | None:
        rows = self._fetch_all(procedure, params)
        return rows[0] if rows else None

    # ------------------------------------------------------------------
    def _execute_scalar(self, sql_batch: str, params: list | None = None):
        params = params or []
        try:
            with self._pool.connection() as connection:
                cursor = connection.cursor()
                cursor.execute(sql_batch, params)
                row = cursor.fetchone()
                return row[0] if row is not None else None
        except pyodbc.Error as exc:
            raise translate_sql_error(exc) from exc

    def _execute(self, sql_batch: str, params: list | None = None) -> None:
        params = params or []
        try:
            with self._pool.connection() as connection:
                cursor = connection.cursor()
                cursor.execute(sql_batch, params)
        except pyodbc.Error as exc:
            raise translate_sql_error(exc) from exc


__all__ = ["BaseRepository", "AppError", "to_snake_case"]
