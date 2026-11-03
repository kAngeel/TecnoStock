"""Pruebas del módulo de categorías."""

from __future__ import annotations

from typing import Any, Callable

from fastapi.testclient import TestClient

from conftest import TEST_CATEGORY_PREFIX


def test_listar_incluye_las_categorias_sembradas(
    client: TestClient, auth: dict[str, str]
) -> None:
    response = client.get("/api/categorias", headers=auth)

    assert response.status_code == 200
    nombres = {categoria["nombre"] for categoria in response.json()}
    assert {"Computadoras", "Componentes", "Periféricos", "Redes", "Almacenamiento"} <= nombres


def test_registrar_y_consultar_categoria(
    client: TestClient,
    auth: dict[str, str],
    crear_categoria: Callable[..., dict[str, Any]],
    suffix: str,
) -> None:
    creada = crear_categoria()

    assert creada["categoria_id"] > 0
    assert creada["nombre"] == f"{TEST_CATEGORY_PREFIX}{suffix}"
    assert creada["total_productos"] == 0

    obtenida = client.get(f"/api/categorias/{creada['categoria_id']}", headers=auth)
    assert obtenida.status_code == 200
    assert obtenida.json()["nombre"] == creada["nombre"]

    listado = client.get("/api/categorias", headers=auth)
    ids = {categoria["categoria_id"] for categoria in listado.json()}
    assert creada["categoria_id"] in ids


def test_nombre_de_categoria_duplicado_devuelve_409(
    client: TestClient,
    auth: dict[str, str],
    crear_categoria: Callable[..., dict[str, Any]],
) -> None:
    creada = crear_categoria()

    response = client.post(
        "/api/categorias",
        headers=auth,
        json={"nombre": creada["nombre"], "descripcion": "Repetida"},
    )

    assert response.status_code == 409
    assert response.json()["code"] == "categoria_duplicada"


def test_actualizar_categoria(
    client: TestClient,
    auth: dict[str, str],
    crear_categoria: Callable[..., dict[str, Any]],
    suffix: str,
) -> None:
    creada = crear_categoria()
    nuevo_nombre = f"{TEST_CATEGORY_PREFIX}EDIT-{suffix}"

    response = client.put(
        f"/api/categorias/{creada['categoria_id']}",
        headers=auth,
        json={"nombre": nuevo_nombre, "descripcion": "Descripción actualizada"},
    )

    assert response.status_code == 200
    assert response.json()["nombre"] == nuevo_nombre
    assert response.json()["descripcion"] == "Descripción actualizada"


def test_categoria_inexistente_devuelve_404(
    client: TestClient, auth: dict[str, str]
) -> None:
    response = client.get("/api/categorias/999999", headers=auth)

    assert response.status_code == 404
    assert response.json()["code"] == "categoria_no_encontrada"


def test_nombre_vacio_es_rechazado(client: TestClient, auth: dict[str, str]) -> None:
    response = client.post(
        "/api/categorias", headers=auth, json={"nombre": "   ", "descripcion": None}
    )

    assert response.status_code == 422
    assert response.json()["code"] == "datos_invalidos"
