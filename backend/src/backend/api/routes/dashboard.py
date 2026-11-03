"""Rutas del dashboard."""

from __future__ import annotations

import datetime as dt
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from backend.api.deps import UsuarioActual, dashboard_service
from backend.schemas.dashboard import DashboardOut
from backend.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "",
    response_model=DashboardOut,
    summary="Indicadores del dashboard (mes actual por defecto)",
)
def obtener(
    _usuario: UsuarioActual,
    service: Annotated[DashboardService, Depends(dashboard_service)],
    fecha_desde: Annotated[dt.date | None, Query()] = None,
    fecha_hasta: Annotated[dt.date | None, Query()] = None,
) -> DashboardOut:
    return service.obtener(fecha_desde, fecha_hasta)
