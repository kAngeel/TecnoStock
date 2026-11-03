"""Repositorio de movimientos de inventario."""

from __future__ import annotations

import datetime as dt

import pyodbc

from backend.core.errors import translate_sql_error
from backend.repositories.base import BaseRepository


class MovimientoRepository(BaseRepository):
    def registrar_entrada(
        self, producto_id: int, usuario_id: int, cantidad: int, motivo: str
    ) -> dict:
        return self._registrar(
            "dbo.usp_MovimientosInventario_RegistrarEntrada",
            producto_id,
            usuario_id,
            cantidad,
            motivo,
        )

    def registrar_salida(
        self, producto_id: int, usuario_id: int, cantidad: int, motivo: str
    ) -> dict:
        return self._registrar(
            "dbo.usp_MovimientosInventario_RegistrarSalida",
            producto_id,
            usuario_id,
            cantidad,
            motivo,
        )

    def _registrar(
        self,
        procedure: str,
        producto_id: int,
        usuario_id: int,
        cantidad: int,
        motivo: str,
    ) -> dict:
        try:
            with self._pool.connection() as connection:
                cursor = connection.cursor()
                cursor.execute(
                    "DECLARE @mov BIGINT, @stock INT; "
                    f"EXEC {procedure} ?, ?, ?, ?, @mov OUTPUT, @stock OUTPUT; "
                    "SELECT @mov AS MovimientoID, @stock AS StockPosterior;",
                    [producto_id, usuario_id, cantidad, motivo],
                )
                row = cursor.fetchone()
                return {"movimiento_id": int(row[0]), "stock_posterior": int(row[1])}
        except pyodbc.Error as exc:
            raise translate_sql_error(exc) from exc

    def listar(
        self,
        fecha_desde: dt.date | None = None,
        fecha_hasta: dt.date | None = None,
        producto_id: int | None = None,
        tipo: str | None = None,
        pagina: int = 1,
        tamano_pagina: int = 20,
    ) -> tuple[list[dict], int]:
        rows = self._fetch_all(
            "dbo.usp_MovimientosInventario_Listar",
            [fecha_desde, fecha_hasta, producto_id, tipo, pagina, tamano_pagina],
        )
        total = int(rows[0]["total_filas"]) if rows else 0
        for row in rows:
            row.pop("total_filas", None)
        return rows, total
