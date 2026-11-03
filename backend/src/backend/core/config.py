"""Configuración central de la aplicación.

Todos los valores sensibles (contraseñas, secreto JWT, credenciales de base
de datos) se leen de variables de entorno o del archivo .env, que nunca se
versiona. Ver .env.example.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(_ENV_FILE, ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Aplicación
    app_name: str = "TecnoStock API"
    environment: str = "development"
    debug: bool = False
    api_prefix: str = "/api"
    host: str = "127.0.0.1"
    port: int = 8000

    # Base de datos
    db_driver: str = "ODBC Driver 18 for SQL Server"
    db_server: str = r".\SQLEXPRESS"
    db_name: str = "TecnoStock"
    db_trusted_connection: bool = True
    db_user: str | None = None
    db_password: str | None = None
    db_encrypt: bool = True
    db_trust_server_certificate: bool = True
    db_timeout: int = Field(default=5, ge=1, le=120)
    db_pool_size: int = Field(default=5, ge=1, le=50)

    # Seguridad
    jwt_secret: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=120, ge=5, le=1440)

    # CORS (lista separada por comas o JSON)
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:4200"]
    )

    # Administrador inicial (opcional). La contraseña se convierte en hash
    # Argon2id al arrancar; nunca se guarda en claro.
    bootstrap_admin_username: str | None = None
    bootstrap_admin_password: str | None = None
    bootstrap_admin_fullname: str = "Administrador"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return []
            if value.startswith("["):
                import json

                return json.loads(value)
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def connection_string(self) -> str:
        """Cadena ODBC para pyodbc.

        En desarrollo se usa autenticación de Windows (Trusted_Connection).
        En producción se definen DB_USER y DB_PASSWORD.
        """
        parts = [
            f"DRIVER={{{self.db_driver}}}",
            f"SERVER={self.db_server}",
            f"DATABASE={self.db_name}",
            "APP=TecnoStock API",
        ]

        if self.db_trusted_connection:
            parts.append("Trusted_Connection=yes")
        else:
            if not self.db_user or not self.db_password:
                raise ValueError(
                    "DB_USER y DB_PASSWORD son obligatorios si "
                    "DB_TRUSTED_CONNECTION es false."
                )
            parts.append(f"UID={self.db_user}")
            parts.append(f"PWD={self.db_password}")

        parts.append(f"Encrypt={'yes' if self.db_encrypt else 'no'}")
        parts.append(
            f"TrustServerCertificate={'yes' if self.db_trust_server_certificate else 'no'}"
        )
        parts.append(f"Connection Timeout={self.db_timeout}")
        return ";".join(parts) + ";"

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"production", "prod"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
