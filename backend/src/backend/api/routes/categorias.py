"""Rutas de categorías."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from backend.api.deps import UsuarioActual, categoria_service
from backend.schemas.categoria import CategoriaCreate, CategoriaOut, CategoriaUpdate
from backend.services.categoria_service import CategoriaService

router = APIRouter(prefix="/categorias", tags=["Categorías"])


@router.get(
    "",
    response_model=list[CategoriaOut],
    summary="Listar categorías",
)
def listar(
    _usuario: UsuarioActual,
    service: Annotated[CategoriaService, Depends(categoria_service)],
) -> list[CategoriaOut]:
    return service.listar()


@router.get(
    "/{categoria_id}",
    response_model=CategoriaOut,
    summary="Obtener una categoría",
)
def obtener(
    categoria_id: int,
    _usuario: UsuarioActual,
    service: Annotated[CategoriaService, Depends(categoria_service)],
) -> CategoriaOut:
    return service.obtener(categoria_id)


@router.post(
    "",
    response_model=CategoriaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar categoría",
)
def crear(
    data: CategoriaCreate,
    _usuario: UsuarioActual,
    service: Annotated[CategoriaService, Depends(categoria_service)],
) -> CategoriaOut:
    return service.crear(data)


@router.put(
    "/{categoria_id}",
    response_model=CategoriaOut,
    summary="Actualizar categoría",
)
def actualizar(
    categoria_id: int,
    data: CategoriaUpdate,
    _usuario: UsuarioActual,
    service: Annotated[CategoriaService, Depends(categoria_service)],
) -> CategoriaOut:
    return service.actualizar(categoria_id, data)
