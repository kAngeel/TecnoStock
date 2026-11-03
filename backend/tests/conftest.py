"""Configuración de las pruebas de integración del backend.

Estas pruebas se ejecutan contra la base de datos TecnoStock real usando el
pool pyodbc de la aplicación. No usan mocks: validan los procedimientos
almacenados, las transacciones y los endpoints HTTP de verdad.

Los datos de prueba se identifican con los prefijos TST- / TSTCAT- y se
eliminan antes y después de la sesión. La limpieza es la única consulta
directa (fuera de procedimientos) y está marcada como exclusiva de pruebas.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Iterator
from typing import Any

import pyodbc
import pytest
from fastapi.testclient import TestClient

from backend.core.config import get_settings
from backend.main import app

TEST_CODE_PREFIX = "TST-"
TEST_CATEGORY_PREFIX = "TSTCAT-"


def _purge_test_data() -> None:
    """Elimina únicamente filas creadas por las pruebas (prefijos TST-)."""
    settings = get_settings()
    with pyodbc.connect(settings.connection_string, autocommit=True) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "DELETE m FROM dbo.MovimientosInventario AS m "
            "INNER JOIN dbo.Productos AS p ON p.ProductoID = m.ProductoID "
            "WHERE p.Codigo LIKE ?",
            (TEST_CODE_PREFIX + "%",),
        )
        cursor.execute(
            "DELETE FROM dbo.Productos WHERE Codigo LIKE ?", (TEST_CODE_PREFIX + "%",)
        )
        cursor.execute(
            "DELETE FROM dbo.Categorias WHERE Nombre LIKE ?",
            (TEST_CATEGORY_PREFIX + "%",),
        )


@pytest.fixture(scope="session", autouse=True)
def _test_data_lifecycle() -> Iterator[None]:
    _purge_test_data()
    yield
    _purge_test_data()


@pytest.fixture(scope="session")
def settings():
    return get_settings()


@pytest.fixture(scope="session")
def client() -> Iterator[TestClient]:
    # El contexto activa el lifespan: inicializa el pool y el administrador.
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def admin_credentials(settings) -> tuple[str, str]:
    username = settings.bootstrap_admin_username
    password = settings.bootstrap_admin_password
    if not username or not password:
        pytest.skip("BOOTSTRAP_ADMIN_* no está configurado en backend/.env")
    return username, password


@pytest.fixture(scope="session")
def token(client: TestClient, admin_credentials: tuple[str, str]) -> str:
    username, password = admin_credentials
    response = client.post(
        "/api/auth/login",
        json={"nombre_usuario": username, "contrasena": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.fixture(scope="session")
def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def usuario(client: TestClient, auth: dict[str, str]) -> dict[str, Any]:
    response = client.get("/api/auth/me", headers=auth)
    assert response.status_code == 200, response.text
    return response.json()


@pytest.fixture
def suffix() -> str:
    return uuid.uuid4().hex[:8].upper()


@pytest.fixture
def crear_categoria(
    client: TestClient, auth: dict[str, str], suffix: str
) -> Callable[..., dict[str, Any]]:
    def _crear(nombre: str | None = None, descripcion: str | None = None) -> dict[str, Any]:
        response = client.post(
            "/api/categorias",
            headers=auth,
            json={
                "nombre": nombre or f"{TEST_CATEGORY_PREFIX}{suffix}",
                "descripcion": descripcion or "Categoría de prueba automatizada",
            },
        )
        assert response.status_code == 201, response.text
        return response.json()

    return _crear


@pytest.fixture
def crear_producto(
    client: TestClient, auth: dict[str, str], suffix: str
) -> Callable[..., dict[str, Any]]:
    def _crear(
        categoria_id: int,
        codigo: str | None = None,
        nombre: str | None = None,
        stock_minimo: int = 2,
        precio_compra: str = "10.50",
        precio_venta: str = "15.00",
        **extra: Any,
    ) -> dict[str, Any]:
        payload = {
            "codigo": codigo or f"{TEST_CODE_PREFIX}{suffix}",
            "nombre": nombre or f"Producto de prueba {suffix}",
            "descripcion": "Producto creado por la suite automatizada",
            "categoria_id": categoria_id,
            "precio_compra": precio_compra,
            "precio_venta": precio_venta,
            "stock_minimo": stock_minimo,
        }
        payload.update(extra)
        response = client.post("/api/productos", headers=auth, json=payload)
        assert response.status_code == 201, response.text
        return response.json()

    return _crear


@pytest.fixture
def entrada(client: TestClient, auth: dict[str, str]) -> Callable[..., Any]:
    def _entrada(producto_id: int, cantidad: int, motivo: str = "Compra de prueba") -> Any:
        return client.post(
            "/api/movimientos/entradas",
            headers=auth,
            json={"producto_id": producto_id, "cantidad": cantidad, "motivo": motivo},
        )

    return _entrada


@pytest.fixture
def salida(client: TestClient, auth: dict[str, str]) -> Callable[..., Any]:
    def _salida(producto_id: int, cantidad: int, motivo: str = "Venta de prueba") -> Any:
        return client.post(
            "/api/movimientos/salidas",
            headers=auth,
            json={"producto_id": producto_id, "cantidad": cantidad, "motivo": motivo},
        )

    return _salida
