"""Servicio de categorías."""

from __future__ import annotations

from backend.core.errors import NotFoundError
from backend.repositories.categoria_repository import CategoriaRepository
from backend.schemas.categoria import CategoriaCreate, CategoriaOut, CategoriaUpdate


class CategoriaService:
    def __init__(self, categorias: CategoriaRepository) -> None:
        self._categorias = categorias

    def listar(self) -> list[CategoriaOut]:
        return [self._to_schema(row) for row in self._categorias.listar()]

    def obtener(self, categoria_id: int) -> CategoriaOut:
        row = self._categorias.obtener(categoria_id)
        if row is None:
            raise NotFoundError("Categoría no encontrada.", "categoria_no_encontrada")
        return self._to_schema(row)

    def crear(self, data: CategoriaCreate) -> CategoriaOut:
        categoria_id = self._categorias.crear(data.nombre, data.descripcion)
        return self.obtener(categoria_id)

    def actualizar(self, categoria_id: int, data: CategoriaUpdate) -> CategoriaOut:
        self._categorias.actualizar(categoria_id, data.nombre, data.descripcion)
        return self.obtener(categoria_id)

    @staticmethod
    def _to_schema(row: dict) -> CategoriaOut:
        return CategoriaOut(
            categoria_id=row["categoria_id"],
            nombre=row["nombre"],
            descripcion=row.get("descripcion"),
            total_productos=int(row.get("total_productos") or 0),
        )
