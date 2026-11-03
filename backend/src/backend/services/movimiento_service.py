"""Servicio de movimientos de inventario."""

from __future__ import annotations

import datetime as dt

from backend.repositories.movimiento_repository import MovimientoRepository
from backend.schemas.movimiento import (
    MovimientoCreate,
    MovimientoOut,
    MovimientoPage,
    MovimientoRegistrado,
)


class MovimientoService:
    def __init__(self, movimientos: MovimientoRepository) -> None:
        self._movimientos = movimientos

    def registrar_entrada(
        self, data: MovimientoCreate, usuario_id: int
    ) -> MovimientoRegistrado:
        resultado = self._movimientos.registrar_entrada(
            data.producto_id, usuario_id, data.cantidad, data.motivo
        )
        return MovimientoRegistrado(
            movimiento_id=resultado["movimiento_id"],
            producto_id=data.producto_id,
            tipo="ENTRADA",
            cantidad=data.cantidad,
            stock_anterior=resultado["stock_posterior"] - data.cantidad,
            stock_posterior=resultado["stock_posterior"],
        )

    def registrar_salida(
        self, data: MovimientoCreate, usuario_id: int
    ) -> MovimientoRegistrado:
        resultado = self._movimientos.registrar_salida(
            data.producto_id, usuario_id, data.cantidad, data.motivo
        )
        return MovimientoRegistrado(
            movimiento_id=resultado["movimiento_id"],
            producto_id=data.producto_id,
            tipo="SALIDA",
            cantidad=data.cantidad,
            stock_anterior=resultado["stock_posterior"] + data.cantidad,
            stock_posterior=resultado["stock_posterior"],
        )

    def listar(
        self,
        fecha_desde: dt.date | None = None,
        fecha_hasta: dt.date | None = None,
        producto_id: int | None = None,
        tipo: str | None = None,
        pagina: int = 1,
        tamano_pagina: int = 20,
    ) -> MovimientoPage:
        rows, total = self._movimientos.listar(
            fecha_desde, fecha_hasta, producto_id, tipo, pagina, tamano_pagina
        )
        items = [
            MovimientoOut(
                movimiento_id=row["movimiento_id"],
                producto_id=row["producto_id"],
                producto_codigo=row["producto_codigo"],
                producto_nombre=row["producto_nombre"],
                usuario_id=row["usuario_id"],
                nombre_usuario=row["nombre_usuario"],
                usuario_nombre_completo=row["usuario_nombre_completo"],
                tipo=row["tipo"],
                cantidad=row["cantidad"],
                motivo=row["motivo"],
                stock_anterior=row["stock_anterior"],
                stock_posterior=row["stock_posterior"],
                fecha=row["fecha"],
            )
            for row in rows
        ]
        total_paginas = (total + tamano_pagina - 1) // tamano_pagina if total else 0
        return MovimientoPage(
            items=items,
            total=total,
            pagina=pagina,
            tamano_pagina=tamano_pagina,
            total_paginas=total_paginas,
        )
