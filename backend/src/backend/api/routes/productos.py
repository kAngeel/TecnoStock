"""Rutas de productos."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from backend.api.deps import UsuarioActual, producto_service
from backend.schemas.producto import (
    ProductoCreate,
    ProductoOut,
    ProductoUpdate,
    StockBajoOut,
)
from backend.services.producto_service import ProductoService

router = APIRouter(prefix="/productos", tags=["Productos"])


@router.get(
    "",
    response_model=list[ProductoOut],
    summary="Listar productos",
)
def listar(
    _usuario: UsuarioActual,
    service: Annotated[ProductoService, Depends(producto_service)],
    busqueda: Annotated[str | None, Query(max_length=150)] = None,
    categoria_id: Annotated[int | None, Query(gt=0)] = None,
    solo_activos: Annotated[bool, Query()] = True,
) -> list[ProductoOut]:
    return service.listar(busqueda, categoria_id, solo_activos)


@router.get(
    "/stock-bajo",
    response_model=list[StockBajoOut],
    summary="Productos activos con stock bajo",
)
def stock_bajo(
    _usuario: UsuarioActual,
    service: Annotated[ProductoService, Depends(producto_service)],
) -> list[StockBajoOut]:
    return service.stock_bajo()


@router.get(
    "/valor-inventario",
    summary="Valor referencial del inventario",
)
def valor_inventario(
    _usuario: UsuarioActual,
    service: Annotated[ProductoService, Depends(producto_service)],
) -> dict:
    return service.valor_inventario()


@router.get(
    "/{producto_id}",
    response_model=ProductoOut,
    summary="Obtener un producto",
)
def obtener(
    producto_id: int,
    _usuario: UsuarioActual,
    service: Annotated[ProductoService, Depends(producto_service)],
) -> ProductoOut:
    return service.obtener(producto_id)


@router.post(
    "",
    response_model=ProductoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar producto (stock inicial 0)",
)
def crear(
    data: ProductoCreate,
    _usuario: UsuarioActual,
    service: Annotated[ProductoService, Depends(producto_service)],
) -> ProductoOut:
    return service.crear(data)


@router.put(
    "/{producto_id}",
    response_model=ProductoOut,
    summary="Actualizar producto (no modifica el stock)",
)
def actualizar(
    producto_id: int,
    data: ProductoUpdate,
    _usuario: UsuarioActual,
    service: Annotated[ProductoService, Depends(producto_service)],
) -> ProductoOut:
    return service.actualizar(producto_id, data)


@router.patch(
    "/{producto_id}/desactivar",
    response_model=ProductoOut,
    summary="Desactivar producto",
)
def desactivar(
    producto_id: int,
    _usuario: UsuarioActual,
    service: Annotated[ProductoService, Depends(producto_service)],
) -> ProductoOut:
    return service.desactivar(producto_id)


@router.patch(
    "/{producto_id}/activar",
    response_model=ProductoOut,
    summary="Reactivar producto",
)
def activar(
    producto_id: int,
    _usuario: UsuarioActual,
    service: Annotated[ProductoService, Depends(producto_service)],
) -> ProductoOut:
    return service.activar(producto_id)
