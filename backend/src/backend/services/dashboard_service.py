"""Servicio del dashboard.

El rango por defecto es el mes actual, tal como se aprobó. El usuario puede
enviar fecha_desde y fecha_hasta para cambiarlo.
"""

from __future__ import annotations

import datetime as dt

from backend.core.errors import BusinessError
from backend.repositories.dashboard_repository import DashboardRepository
from backend.schemas.dashboard import (
    DashboardOut,
    DashboardResumen,
    MovimientoPorDia,
    TopProducto,
    UltimoMovimiento,
)


class DashboardService:
    def __init__(self, dashboard: DashboardRepository) -> None:
        self._dashboard = dashboard

    def obtener(
        self,
        fecha_desde: dt.date | None = None,
        fecha_hasta: dt.date | None = None,
    ) -> DashboardOut:
        hoy = dt.date.today()
        if fecha_desde is None:
            fecha_desde = hoy.replace(day=1)
        if fecha_hasta is None:
            fecha_hasta = hoy

        if fecha_desde > fecha_hasta:
            raise BusinessError(
                "La fecha inicial no puede ser posterior a la fecha final.",
                "rango_fechas_invalido",
            )

        resumen_row = self._dashboard.resumen(fecha_desde, fecha_hasta)
        serie_rows = self._dashboard.movimientos_por_dia(fecha_desde, fecha_hasta)
        top_rows = self._dashboard.top_productos(fecha_desde, fecha_hasta, 5)
        ultimos_rows = self._dashboard.ultimos_movimientos(8)

        return DashboardOut(
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            resumen=DashboardResumen(
                productos_activos=int(resumen_row.get("productos_activos") or 0),
                productos_inactivos=int(resumen_row.get("productos_inactivos") or 0),
                productos_total=int(resumen_row.get("productos_total") or 0),
                categorias_total=int(resumen_row.get("categorias_total") or 0),
                productos_stock_bajo=int(resumen_row.get("productos_stock_bajo") or 0),
                valor_inventario=resumen_row.get("valor_inventario") or 0,
                unidades_en_stock=int(resumen_row.get("unidades_en_stock") or 0),
                movimientos_periodo=int(resumen_row.get("movimientos_periodo") or 0),
                unidades_entrada=int(resumen_row.get("unidades_entrada") or 0),
                unidades_salida=int(resumen_row.get("unidades_salida") or 0),
            ),
            serie_diaria=[
                MovimientoPorDia(
                    fecha=row["fecha"],
                    unidades_entrada=int(row["unidades_entrada"]),
                    unidades_salida=int(row["unidades_salida"]),
                    movimientos=int(row["movimientos"]),
                )
                for row in serie_rows
            ],
            top_productos=[
                TopProducto(
                    producto_id=row["producto_id"],
                    codigo=row["codigo"],
                    nombre=row["nombre"],
                    unidades_entrada=int(row["unidades_entrada"]),
                    unidades_salida=int(row["unidades_salida"]),
                    movimientos=int(row["movimientos"]),
                )
                for row in top_rows
            ],
            ultimos_movimientos=[
                UltimoMovimiento(
                    movimiento_id=row["movimiento_id"],
                    fecha=row["fecha"],
                    tipo=row["tipo"],
                    cantidad=row["cantidad"],
                    motivo=row["motivo"],
                    stock_anterior=row["stock_anterior"],
                    stock_posterior=row["stock_posterior"],
                    producto_codigo=row["producto_codigo"],
                    producto_nombre=row["producto_nombre"],
                    nombre_usuario=row["nombre_usuario"],
                )
                for row in ultimos_rows
            ],
        )
