"""Repositorio de usuarios."""

from __future__ import annotations

from backend.repositories.base import BaseRepository


class UsuarioRepository(BaseRepository):
    def obtener_por_nombre(self, nombre_usuario: str) -> dict | None:
        return self._fetch_one(
            "dbo.usp_Usuarios_ObtenerPorNombreUsuario", [nombre_usuario]
        )

    def obtener_por_id(self, usuario_id: int) -> dict | None:
        return self._fetch_one("dbo.usp_Usuarios_ObtenerPorID", [usuario_id])

    def listar(self) -> list[dict]:
        return self._fetch_all("dbo.usp_Usuarios_Listar")

    def crear(
        self, nombre_usuario: str, nombre_completo: str, clave_hash: str
    ) -> int:
        return int(
            self._execute_scalar(
                "DECLARE @id INT; "
                "EXEC dbo.usp_Usuarios_Insertar ?, ?, ?, @id OUTPUT; "
                "SELECT @id;",
                [nombre_usuario, nombre_completo, clave_hash],
            )
        )

    def actualizar_hash(self, usuario_id: int, clave_hash: str) -> None:
        self._execute(
            "EXEC dbo.usp_Usuarios_ActualizarClaveHash ?, ?",
            [usuario_id, clave_hash],
        )
