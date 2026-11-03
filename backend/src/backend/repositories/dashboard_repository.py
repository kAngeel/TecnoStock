"""Repositorio del dashboard."""

from __future__ import annotations

import datetime as dt

from backend.repositories.base import BaseRepository


class DashboardRepository(BaseRepository):
    def resumen(self, fecha_desde: dt.date | None, fecha_hasta: dt.date | None) -> dict:
        row = self._fetch_one(
            "dbo.usp_Dashboard_Resumen", [fecha_desde, fecha_hasta]
        )
        return row or {}

    def movimientos_por_dia(
        self, fecha_desde: dt.date | None, fecha_hasta: dt.date | None
    ) -> list[dict]:
        return self._fetch_all(
            "dbo.usp_Dashboard_MovimientosPorDia", [fecha_desde, fecha_hasta]
        )

    def top_productos(
        self, fecha_desde: dt.date | None, fecha_hasta: dt.date | None, top: int = 5
    ) -> list[dict]:
        return self._fetch_all(
            "dbo.usp_Dashboard_TopProductos", [fecha_desde, fecha_hasta, top]
        )

    def ultimos_movimientos(self, top: int = 8) -> list[dict]:
        return self._fetch_all("dbo.usp_Dashboard_UltimosMovimientos", [top])
