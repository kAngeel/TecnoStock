"""Rutas de movimientos de inventario."""

from __future__ import annotations

import datetime as dt
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, status

from backend.api.deps import UsuarioActual, movimiento_service
from backend.schemas.movimiento import (
    MovimientoCreate,
    MovimientoPage,
    MovimientoRegistrado,
)
from backend.services.movimiento_service import MovimientoService

router = APIRouter(prefix="/movimientos", tags=["Movimientos"])


@router.get(
    "",
    response_model=MovimientoPage,
    summary="Consultar historial de movimientos",
)
def listar(
    _usuario: UsuarioActual,
    service: Annotated[MovimientoService, Depends(movimiento_service)],
    fecha_desde: Annotated[dt.date | None, Query()] = None,
    fecha_hasta: Annotated[dt.date | None, Query()] = None,
    producto_id: Annotated[int | None, Query(gt=0)] = None,
    tipo: Annotated[Literal["ENTRADA", "SALIDA"] | None, Query()] = None,
    pagina: Annotated[int, Query(ge=1)] = 1,
    tamano_pagina: Annotated[int, Query(ge=1, le=100)] = 20,
) -> MovimientoPage:
    return service.listar(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        producto_id=producto_id,
        tipo=tipo,
        pagina=pagina,
        tamano_pagina=tamano_pagina,
    )


@router.post(
    "/entradas",
    response_model=MovimientoRegistrado,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar entrada de inventario",
)
def entrada(
    data: MovimientoCreate,
    usuario: UsuarioActual,
    service: Annotated[MovimientoService, Depends(movimiento_service)],
) -> MovimientoRegistrado:
    return service.registrar_entrada(data, usuario.usuario_id)


@router.post(
    "/salidas",
    response_model=MovimientoRegistrado,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar salida de inventario",
)
def salida(
    data: MovimientoCreate,
    usuario: UsuarioActual,
    service: Annotated[MovimientoService, Depends(movimiento_service)],
) -> MovimientoRegistrado:
    return service.registrar_salida(data, usuario.usuario_id)
