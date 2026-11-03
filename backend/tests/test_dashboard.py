"""Pruebas de los indicadores del dashboard."""

from __future__ import annotations

import datetime as dt
from typing import Any, Callable

from fastapi.testclient import TestClient


def test_rango_por_defecto_es_el_mes_actual(client: TestClient, auth: dict[str, str]) -> None:
    response = client.get("/api/dashboard", headers=auth)

    assert response.status_code == 200
    body = response.json()
    hoy = dt.date.today()
    assert body["fecha_desde"] == hoy.replace(day=1).isoformat()
    assert body["fecha_hasta"] == hoy.isoformat()


def test_rango_personalizado(client: TestClient, auth: dict[str, str]) -> None:
    response = client.get(
        "/api/dashboard",
        params={"fecha_desde": "2026-01-01", "fecha_hasta": "2026-01-31"},
        headers=auth,
    )

    assert response.status_code == 200
    assert response.json()["fecha_desde"] == "2026-01-01"
    assert response.json()["fecha_hasta"] == "2026-01-31"


def test_rango_invertido_es_rechazado(client: TestClient, auth: dict[str, str]) -> None:
    response = client.get(
        "/api/dashboard",
        params={"fecha_desde": "2026-05-10", "fecha_hasta": "2026-05-01"},
        headers=auth,
    )

    assert response.status_code == 422
    assert response.json()["code"] == "rango_fechas_invalido"


def test_indicadores_reflejan_los_movimientos(
    client: TestClient,
    auth: dict[str, str],
    crear_categoria: Callable[..., dict[str, Any]],
    crear_producto: Callable[..., dict[str, Any]],
    entrada: Callable[..., Any],
    salida: Callable[..., Any],
) -> None:
    hoy = dt.date.today().isoformat()
    antes = client.get(
        "/api/dashboard", params={"fecha_desde": hoy, "fecha_hasta": hoy}, headers=auth
    ).json()["resumen"]

    categoria = crear_categoria()
    producto = crear_producto(categoria["categoria_id"], stock_minimo=10)
    assert entrada(producto["producto_id"], 6, "Entrada para dashboard").status_code == 201
    assert salida(producto["producto_id"], 2, "Salida para dashboard").status_code == 201

    despues = client.get(
        "/api/dashboard", params={"fecha_desde": hoy, "fecha_hasta": hoy}, headers=auth
    ).json()["resumen"]

    assert despues["movimientos_periodo"] - antes["movimientos_periodo"] == 2
    assert despues["unidades_entrada"] - antes["unidades_entrada"] == 6
    assert despues["unidades_salida"] - antes["unidades_salida"] == 2
    assert despues["productos_activos"] - antes["productos_activos"] == 1
    assert despues["unidades_en_stock"] - antes["unidades_en_stock"] == 4

    # El producto quedó con stock 4 y stock mínimo 10: figura en stock bajo.
    assert despues["productos_stock_bajo"] >= antes["productos_stock_bajo"]

    # El valor del inventario del dashboard coincide con el de los productos.
    productos = client.get(
        "/api/productos", params={"solo_activos": False}, headers=auth
    ).json()
    valor_calculado = round(
        sum(item["stock"] * item["precio_compra"] for item in productos), 2
    )
    assert abs(despues["valor_inventario"] - valor_calculado) < 0.01


def test_serie_diaria_y_ultimos_movimientos(
    client: TestClient,
    auth: dict[str, str],
    crear_categoria: Callable[..., dict[str, Any]],
    crear_producto: Callable[..., dict[str, Any]],
    entrada: Callable[..., Any],
) -> None:
    categoria = crear_categoria()
    producto = crear_producto(categoria["categoria_id"])
    assert entrada(producto["producto_id"], 3, "Entrada para serie diaria").status_code == 201

    hoy = dt.date.today()
    body = client.get(
        "/api/dashboard",
        params={"fecha_desde": hoy.isoformat(), "fecha_hasta": hoy.isoformat()},
        headers=auth,
    ).json()

    assert body["serie_diaria"], "La serie diaria no puede estar vacía tras un movimiento"
    dia = next(item for item in body["serie_diaria"] if item["fecha"] == hoy.isoformat())
    assert dia["unidades_entrada"] >= 3
    assert dia["movimientos"] >= 1

    ultimo = body["ultimos_movimientos"][0]
    assert ultimo["producto_codigo"] == producto["codigo"]
    assert ultimo["tipo"] in {"ENTRADA", "SALIDA"}
    assert ultimo["nombre_usuario"]

    for item in body["top_productos"]:
        assert item["unidades_entrada"] >= 0
        assert item["unidades_salida"] >= 0
