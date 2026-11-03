"""Repositorio de categorías."""

from __future__ import annotations

from backend.repositories.base import BaseRepository


class CategoriaRepository(BaseRepository):
    def listar(self) -> list[dict]:
        return self._fetch_all("dbo.usp_Categorias_Listar")

    def obtener(self, categoria_id: int) -> dict | None:
        return self._fetch_one("dbo.usp_Categorias_Obtener", [categoria_id])

    def crear(self, nombre: str, descripcion: str | None) -> int:
        return int(
            self._execute_scalar(
                "DECLARE @id INT; "
                "EXEC dbo.usp_Categorias_Insertar ?, ?, @id OUTPUT; "
                "SELECT @id;",
                [nombre, descripcion],
            )
        )

    def actualizar(self, categoria_id: int, nombre: str, descripcion: str | None) -> None:
        self._execute(
            "EXEC dbo.usp_Categorias_Actualizar ?, ?, ?",
            [categoria_id, nombre, descripcion],
        )
