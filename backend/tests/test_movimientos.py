"""Pruebas de entradas, salidas e historial de movimientos."""

from __future__ import annotations

import datetime as dt
from typing import Any, Callable

from fastapi.testclient import TestClient


def test_entrada_y_salida_actualizan_el_stock(
    client: TestClient,
    auth: dict[str, str],
    crear_categoria: Callable[..., dict[str, Any]],
    crear_producto: Callable[..., dict[str, Any]],
    entrada: Callable[..., Any],
    salida: Callable[..., Any],
) -> None:
    categoria = crear_categoria()
    producto = crear_producto(categoria["categoria_id"])

    alta = entrada(producto["producto_id"], 10, "Compra inicial")
    assert alta.status_code == 201
    cuerpo = alta.json()
    assert cuerpo["tipo"] == "ENTRADA"
    assert cuerpo["cantidad"] == 10
    assert cuerpo["stock_anterior"] == 0
    assert cuerpo["stock_posterior"] == 10
    assert cuerpo["movimiento_id"] > 0

    baja = salida(producto["producto_id"], 3, "Venta al cliente")
    assert baja.status_code == 201
    cuerpo = baja.json()
    assert cuerpo["tipo"] == "SALIDA"
    assert cuerpo["stock_anterior"] == 10
    assert cuerpo["stock_posterior"] == 7

    actual = client.get(f"/api/productos/{producto['producto_id']}", headers=auth)
    assert actual.json()["stock"] == 7
    assert actual.json()["valor_inventario"] == round(7 * 10.50, 2)


def test_salida_mayor_al_stock_es_rechazada(
    client: TestClient,
    auth: dict[str, str],
    crear_categoria: Callable[..., dict[str, Any]],
    crear_producto: Callable[..., dict[str, Any]],
    entrada: Callable[..., Any],
    salida: Callable[..., Any],
) -> None:
    categoria = crear_categoria()
    producto = crear_producto(categoria["categoria_id"])
    assert entrada(producto["producto_id"], 5).status_code == 201

    response = salida(producto["producto_id"], 6)

    assert response.status_code == 409
    assert response.json()["code"] == "stock_insuficiente"

    actual = client.get(f"/api/productos/{producto['producto_id']}", headers=auth)
    assert actual.json()["stock"] == 5

    # La transacción no dejó historial de la salida fallida.
    historial = client.get(
        "/api/movimientos",
        params={"producto_id": producto["producto_id"]},
        headers=auth,
    )
    assert historial.json()["total"] == 1
    assert historial.json()["items"][0]["tipo"] == "ENTRADA"


def test_cantidad_y_motivo_invalidos(
    client: TestClient,
    auth: dict[str, str],
    crear_categoria: Callable[..., dict[str, Any]],
    crear_producto: Callable[..., dict[str, Any]],
    entrada: Callable[..., Any],
) -> None:
    categoria = crear_categoria()
    producto = crear_producto(categoria["categoria_id"])

    cantidad_cero = entrada(producto["producto_id"], 0)
    assert cantidad_cero.status_code == 422
    assert cantidad_cero.json()["code"] == "datos_invalidos"

    motivo_vacio = client.post(
        "/api/movimientos/entradas",
        headers=auth,
        json={
            "producto_id": producto["producto_id"],
            "cantidad": 1,
            "motivo": "   ",
        },
    )
    assert motivo_vacio.status_code == 422


def test_producto_inexistente_en_movimiento(
    entrada: Callable[..., Any],
) -> None:
    response = entrada(999999, 1)

    assert response.status_code == 409
    assert response.json()["code"] == "producto_no_disponible"


def test_historial_conserva_todos_los_datos(
    client: TestClient,
    auth: dict[str, str],
    crear_categoria: Callable[..., dict[str, Any]],
    crear_producto: Callable[..., dict[str, Any]],
    entrada: Callable[..., Any],
    salida: Callable[..., Any],
    usuario: dict[str, Any],
) -> None:
    categoria = crear_categoria()
    producto = crear_producto(categoria["categoria_id"])
    assert entrada(producto["producto_id"], 8, "Ingreso de mercadería").status_code == 201
    assert salida(producto["producto_id"], 2, "Despacho a tienda").status_code == 201

    response = client.get(
        "/api/movimientos",
        params={"producto_id": producto["producto_id"]},
        headers=auth,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["pagina"] == 1
    assert body["total_paginas"] == 1

    salida_registrada = body["items"][0]
    assert salida_registrada["tipo"] == "SALIDA"
    assert salida_registrada["cantidad"] == 2
    assert salida_registrada["motivo"] == "Despacho a tienda"
    assert salida_registrada["stock_anterior"] == 8
    assert salida_registrada["stock_posterior"] == 6
    assert salida_registrada["producto_codigo"] == producto["codigo"]
    assert salida_registrada["nombre_usuario"] == usuario["nombre_usuario"]
    assert salida_registrada["fecha"]

    entrada_registrada = body["items"][1]
    assert entrada_registrada["tipo"] == "ENTRADA"
    assert entrada_registrada["stock_anterior"] == 0
    assert entrada_registrada["stock_posterior"] == 8


def test_historial_filtra_por_tipo_y_pagina(
    client: TestClient,
    auth: dict[str, str],
    crear_categoria: Callable[..., dict[str, Any]],
    crear_producto: Callable[..., dict[str, Any]],
    entrada: Callable[..., Any],
    salida: Callable[..., Any],
) -> None:
    categoria = crear_categoria()
    producto = crear_producto(categoria["categoria_id"])
    assert entrada(producto["producto_id"], 10).status_code == 201
    assert salida(producto["producto_id"], 1).status_code == 201
    assert salida(producto["producto_id"], 2).status_code == 201

    solo_salidas = client.get(
        "/api/movimientos",
        params={"producto_id": producto["producto_id"], "tipo": "SALIDA"},
        headers=auth,
    )
    assert solo_salidas.status_code == 200
    assert solo_salidas.json()["total"] == 2
    assert {item["tipo"] for item in solo_salidas.json()["items"]} == {"SALIDA"}

    paginado = client.get(
        "/api/movimientos",
        params={
            "producto_id": producto["producto_id"],
            "pagina": 2,
            "tamano_pagina": 2,
        },
        headers=auth,
    )
    assert paginado.status_code == 200
    body = paginado.json()
    assert body["total"] == 3
    assert body["pagina"] == 2
    assert body["total_paginas"] == 2
    assert len(body["items"]) == 1


def test_historial_filtra_por_fecha(
    client: TestClient,
    auth: dict[str, str],
    crear_categoria: Callable[..., dict[str, Any]],
    crear_producto: Callable[..., dict[str, Any]],
    entrada: Callable[..., Any],
) -> None:
    categoria = crear_categoria()
    producto = crear_producto(categoria["categoria_id"])
    assert entrada(producto["producto_id"], 4).status_code == 201

    hoy = dt.date.today()
    dentro = client.get(
        "/api/movimientos",
        params={
            "producto_id": producto["producto_id"],
            "fecha_desde": hoy.isoformat(),
            "fecha_hasta": hoy.isoformat(),
        },
        headers=auth,
    )
    assert dentro.status_code == 200
    assert dentro.json()["total"] == 1

    ayer = (hoy - dt.timedelta(days=1)).isoformat()
    fuera = client.get(
        "/api/movimientos",
        params={
            "producto_id": producto["producto_id"],
            "fecha_desde": ayer,
            "fecha_hasta": ayer,
        },
        headers=auth,
    )
    assert fuera.status_code == 200
    assert fuera.json()["total"] == 0


def test_tipo_de_movimiento_invalido_en_filtro(
    client: TestClient, auth: dict[str, str]
) -> None:
    response = client.get(
        "/api/movimientos", params={"tipo": "AJUSTE"}, headers=auth
    )

    assert response.status_code == 422
