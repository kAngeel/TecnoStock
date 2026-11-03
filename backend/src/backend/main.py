"""Aplicación FastAPI de TecnoStock."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.router import api_router
from backend.core.config import get_settings
from backend.core.database import close_pool, get_pool, init_pool
from backend.core.errors import AppError, translate_sql_error
from backend.repositories.usuario_repository import UsuarioRepository
from backend.services.auth_service import AuthService

logger = logging.getLogger("backend")

_VALIDATION_MESSAGES = {
    "Field required": "Este campo es obligatorio.",
    "Input should be a valid integer": "Debe ser un número entero.",
    "Input should be a valid number": "Debe ser un número válido.",
    "Input should be a valid boolean": "Debe ser verdadero o falso.",
    "Input should be a valid date": "Debe ser una fecha válida (AAAA-MM-DD).",
    "Input should be a valid datetime": "Debe ser una fecha y hora válida.",
}


def _traducir_error(error: dict[str, Any]) -> str:
    msg = str(error.get("msg", "Dato inválido."))
    ctx = error.get("ctx") or {}

    if msg in _VALIDATION_MESSAGES:
        return _VALIDATION_MESSAGES[msg]

    if msg.startswith("String should have at least"):
        return f"Debe tener al menos {ctx.get('min_length')} caracteres."
    if msg.startswith("String should have at most"):
        return f"Debe tener como máximo {ctx.get('max_length')} caracteres."
    if msg.startswith("Input should be greater than"):
        return f"Debe ser mayor que {ctx.get('gt')}."
    if msg.startswith("Input should be greater than or equal to"):
        return f"Debe ser mayor o igual que {ctx.get('ge')}."
    if msg.startswith("Input should be less than"):
        return f"Debe ser menor que {ctx.get('lt')}."
    if msg.startswith("Input should be less than or equal to"):
        return f"Debe ser menor o igual que {ctx.get('le')}."
    if msg.startswith("Decimal input should have no more than"):
        return "Debe tener como máximo 2 decimales."

    return msg


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    logging.basicConfig(
        level=logging.DEBUG if settings.debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    pool = init_pool(settings)

    try:
        AuthService(UsuarioRepository(pool), settings).asegurar_administrador_inicial()
    except Exception:
        logger.exception(
            "No se pudo crear el administrador inicial. "
            "Verifique la conexión y los scripts de base de datos."
        )

    logger.info("TecnoStock API iniciada (entorno=%s).", settings.environment)
    try:
        yield
    finally:
        close_pool()
        logger.info("TecnoStock API detenida.")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description=(
            "API de inventario TecnoStock. Acceso a datos exclusivamente "
            "mediante procedimientos almacenados de SQL Server."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def _app_error_handler(_request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.message,
                "code": exc.code,
                "details": exc.details,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(_request: Request, exc: RequestValidationError):
        errores = []
        for error in exc.errors():
            campo = ".".join(
                str(part) for part in error.get("loc", ()) if part not in ("body", "query")
            )
            errores.append(
                {
                    "campo": campo or None,
                    "mensaje": _traducir_error(error),
                    "tipo": error.get("type"),
                }
            )
        primero = errores[0]["mensaje"] if errores else "Datos inválidos."
        return JSONResponse(
            status_code=422,
            content={
                "detail": primero,
                "code": "datos_invalidos",
                "details": errores,
            },
        )

    @app.exception_handler(Exception)
    async def _unhandled_handler(_request: Request, exc: Exception):
        if isinstance(exc, AppError):
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.message, "code": exc.code},
            )
        traducido = translate_sql_error(exc)
        if traducido.status_code < 500:
            return JSONResponse(
                status_code=traducido.status_code,
                content={"detail": traducido.message, "code": traducido.code},
            )
        logger.exception("Error no controlado")
        return JSONResponse(
            status_code=traducido.status_code,
            content={"detail": traducido.message, "code": traducido.code},
        )

    app.include_router(api_router, prefix=settings.api_prefix)

    @app.get("/", tags=["Sistema"], summary="Información de la API")
    def root() -> dict:
        return {
            "app": settings.app_name,
            "version": "1.0.0",
            "docs": "/docs",
            "api": settings.api_prefix,
        }

    @app.get("/api/health", tags=["Sistema"], summary="Estado del servicio")
    def health() -> dict:
        try:
            ok = get_pool().healthcheck()
        except Exception:
            logger.exception("Healthcheck de base de datos fallido")
            return JSONResponse(  # type: ignore[return-value]
                status_code=503,
                content={"status": "degradado", "database": "no disponible"},
            )
        return {
            "status": "ok" if ok else "degradado",
            "database": "ok" if ok else "no disponible",
            "version": "1.0.0",
        }

    return app


app = create_app()


def run() -> None:
    settings = get_settings()
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    run()
