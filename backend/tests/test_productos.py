"""Pruebas del módulo de productos.

Reglas cubiertas:
  - El stock inicial siempre es 0 y no se puede fijar desde el alta/edición.
  - Las ediciones no modifican el stock y sí actualizan FechaActualizacion.
  - Los productos inactivos no admiten movimientos ni aparecen en stock bajo.
  - El valor del inventario incluye productos inactivos con existencias.
"""

from __future__ import annotations

from typing import Any, Callable

from fastapi.testclient import TestClient

from conftest import TEST_CODE_PREFIX


def test_producto_nuevo_empieza_con_stock_cero(
    client: TestClient,
    auth: dict[str, str],
    crear_categoria: Callable[..., dict[str, Any]],
    crear_producto: Callable[..., dict[str, Any]],
) -> None:
    categoria = crear_categoria()
    producto = crear_producto(categoria["categoria_id"])

    assert producto["stock"] == 0
    assert producto["activo"] is True
    assert producto["valor_inventario"] == 0
    assert producto["stock_bajo"] is True
    assert producto["precio_compra"] == 10.5
    assert producto["precio_venta"] == 15.0
    assert producto["categoria_nombre"] == categoria["nombre"]


def test_stock_enviado_en_el_alta_es_ignorado(
    client: TestClient,
    auth: dict[str, str],
    crear_categoria: Callable[..., dict[str, Any]],
    crear_producto: Callable[..., dict[str, Any]],
) -> None:
    categoria = crear_categoria()
    producto = crear_producto(categoria["categoria_id"], stock=500, stock_minimo=1)

    assert producto["stock"] == 0

    obtenido = client.get(f"/api/productos/{producto['producto_id']}", headers=auth)
    assert obtenido.json()["stock"] == 0


def test_codigo_duplicado_devuelve_409(
    client: TestClient,
    auth: dict[str, str],
    crear_categoria: Callable[..., dict[str, Any]],
    crear_producto: Callable[..., dict[str, Any]],
) -> None:
    categoria = crear_categoria()
    producto = crear_producto(categoria["categoria_id"])

    response = client.post(
        "/api/productos",
        headers=auth,
        json={
            "codigo": producto["codigo"],
            "nombre": "Otro producto",
            "descripcion": "Código repetido",
            "categoria_id": categoria["categoria_id"],
            "precio_compra": "5.00",
            "precio_venta": "8.00",
            "stock_minimo": 1,
        },
    )

    assert response.status_code == 409
    assert response.json()["code"] == "producto_duplicado"


def test_categoria_inexistente_devuelve_422(
    client: TestClient, auth: dict[str, str], suffix: str
) -> None:
    response = client.post(
        "/api/productos",
        headers=auth,
        json={
            "codigo": f"{TEST_CODE_PREFIX}NC-{suffix}",
            "nombre": "Producto sin categoría",
            "descripcion": "La categoría no existe",
            "categoria_id": 999999,
            "precio_compra": "5.00",
            "precio_venta": "8.00",
            "stock_minimo": 1,
        },
    )

    assert response.status_code == 422
    assert response.json()["code"] == "categoria_no_encontrada"


def test_validaciones_de_precio_y_descripcion(
    client: TestClient,
    auth: dict[str, str],
    crear_categoria: Callable[..., dict[str, Any]],
    suffix: str,
) -> None:
    categoria = crear_categoria()
    base = {
        "codigo": f"{TEST_CODE_PREFIX}V-{suffix}",
        "nombre": "Producto inválido",
        "descripcion": "Válida",
        "categoria_id": categoria["categoria_id"],
        "precio_compra": "10.00",
        "precio_venta": "12.00",
        "stock_minimo": 1,
    }

    precio_cero = client.post(
        "/api/productos", headers=auth, json={**base, "precio_compra": "0"}
    )
    assert precio_cero.status_code == 422
    assert precio_cero.json()["code"] == "datos_invalidos"

    descripcion_vacia = client.post(
        "/api/productos", headers=auth, json={**base, "descripcion": "   "}
    )
    assert descripcion_vacia.status_code == 422

    stock_minimo_negativo = client.post(
        "/api/productos", headers=auth, json={**base, "stock_minimo": -1}
    )
    assert stock_minimo_negativo.status_code == 422


def test_actualizar_producto_no_modifica_el_stock(
    client: TestClient,
    auth: dict[str, str],
    crear_categoria: Callable[..., dict[str, Any]],
    crear_producto: Callable[..., dict[str, Any]],
    entrada: Callable[..., Any],
) -> None:
    categoria = crear_categoria()
    producto = crear_producto(categoria["categoria_id"])

    assert entrada(producto["producto_id"], 7).status_code == 201

    response = client.put(
        f"/api/productos/{producto['producto_id']}",
        headers=auth,
        json={
            "codigo": producto["codigo"],
            "nombre": "Nombre actualizado",
            "descripcion": "Descripción actualizada del producto",
            "categoria_id": categoria["categoria_id"],
            "precio_compra": "11.00",
            "precio_venta": "16.00",
            "stock_minimo": 3,
            "stock": 999,
        },
    )

    assert response.status_code == 200
    actualizado = response.json()
    assert actualizado["nombre"] == "Nombre actualizado"
    assert actualizado["precio_compra"] == 11.0
    assert actualizado["stock"] == 7
    assert actualizado["fecha_actualizacion"] >= producto["fecha_creacion"]


def test_desactivar_producto(
    client: TestClient,
    auth: dict[str, str],
    crear_categoria: Callable[..., dict[str, Any]],
    crear_producto: Callable[..., dict[str, Any]],
    entrada: Callable[..., Any],
    salida: Callable[..., Any],
) -> None:
    categoria = crear_categoria()
    producto = crear_producto(categoria["categoria_id"], stock_minimo=5)
    assert entrada(producto["producto_id"], 2).status_code == 201

    desactivado = client.patch(
        f"/api/productos/{producto['producto_id']}/desactivar", headers=auth
    )
    assert desactivado.status_code == 200
    assert desactivado.json()["activo"] is False
    assert desactivado.json()["stock"] == 2

    # No aparece en el listado por defecto (solo activos)...
    activos = client.get("/api/productos", headers=auth)
    assert producto["producto_id"] not in {
        item["producto_id"] for item in activos.json()
    }

    # ...pero sí al pedir inactivos.
    todos = client.get("/api/productos", params={"solo_activos": False}, headers=auth)
    assert producto["producto_id"] in {item["producto_id"] for item in todos.json()}

    # Un producto inactivo no admite movimientos.
    rechazada = salida(producto["producto_id"], 1)
    assert rechazada.status_code == 409
    assert rechazada.json()["code"] == "producto_no_disponible"

    # El stock bajo solo considera activos.
    stock_bajo = client.get("/api/productos/stock-bajo", headers=auth)
    assert producto["producto_id"] not in {
        item["producto_id"] for item in stock_bajo.json()
    }

    # El valor del inventario sí incluye el inactivo con existencias (2 x 10.50).
    valor = client.get("/api/productos/valor-inventario", headers=auth)
    assert valor.status_code == 200
    assert valor.json()["unidades_en_stock"] >= 2
    # El dinero debe viajar como número JSON, no como cadena decimal.
    assert isinstance(valor.json()["valor_inventario"], float)
    assert isinstance(valor.json()["productos_con_stock"], int)

    reactivado = client.patch(
        f"/api/productos/{producto['producto_id']}/activar", headers=auth
    )
    assert reactivado.status_code == 200
    assert reactivado.json()["activo"] is True


def test_producto_inexistente_devuelve_404(
    client: TestClient, auth: dict[str, str]
) -> None:
    response = client.get("/api/productos/999999", headers=auth)

    assert response.status_code == 404
    assert response.json()["code"] == "producto_no_encontrado"


def test_busqueda_y_filtro_por_categoria(
    client: TestClient,
    auth: dict[str, str],
    crear_categoria: Callable[..., dict[str, Any]],
    crear_producto: Callable[..., dict[str, Any]],
    suffix: str,
) -> None:
    categoria = crear_categoria()
    producto = crear_producto(
        categoria["categoria_id"], codigo=f"{TEST_CODE_PREFIX}BUS-{suffix}"
    )

    por_categoria = client.get(
        "/api/productos", params={"categoria_id": categoria["categoria_id"]}, headers=auth
    )
    assert por_categoria.status_code == 200
    assert [item["producto_id"] for item in por_categoria.json()] == [
        producto["producto_id"]
    ]

    por_texto = client.get(
        "/api/productos", params={"busqueda": f"BUS-{suffix}"}, headers=auth
    )
    assert por_texto.status_code == 200
    assert [item["producto_id"] for item in por_texto.json()] == [
        producto["producto_id"]
    ]

    sin_resultados = client.get(
        "/api/productos", params={"busqueda": "no-existe-xyz"}, headers=auth
    )
    assert sin_resultados.status_code == 200
    assert sin_resultados.json() == []
