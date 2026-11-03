"""Agregador de rutas de la API."""

from fastapi import APIRouter

from backend.api.routes import auth, categorias, dashboard, movimientos, productos

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(categorias.router)
api_router.include_router(productos.router)
api_router.include_router(movimientos.router)
api_router.include_router(dashboard.router)
