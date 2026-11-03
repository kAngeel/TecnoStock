"""Prueba de concurrencia: el stock nunca puede quedar negativo.

Se lanzan 20 salidas simultáneas de 1 unidad contra un producto con stock 10.
El procedimiento usa UPDLOCK/ROWLOCK dentro de una transacción, por lo que
solo 10 deben confirmarse y las otras 10 deben rechazarse con stock
insuficiente, sin dejar el stock por debajo de cero ni filas inconsistentes.

Las llamadas van directas al repositorio (mismo pool pyodbc que usa la API)
para que la concurrencia sea real y no simulada por el cliente HTTP de test.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

from fastapi.testclient import TestClient

from backend.core.database import get_pool
from backend.repositories.movimiento_repository import MovimientoRepository


def test_salidas_concurrentes_no_dejan_stock_negativo(
    client: TestClient,
    auth: dict[str, str],
    usuario: dict[str, Any],
    crear_categoria: Callable[..., dict[str, Any]],
    crear_producto: Callable[..., dict[str, Any]],
    entrada: Callable[..., Any],
) -> None:
    categoria = crear_categoria()
    producto = crear_producto(categoria["categoria_id"])
    producto_id = producto["producto_id"]

    assert entrada(producto_id, 10, "Stock inicial para concurrencia").status_code == 201

    repositorio = MovimientoRepository(get_pool())

    def intentar_salida(_: int) -> str:
        try:
            repositorio.registrar_salida(producto_id, usuario["usuario_id"], 1, "Salida concurrente")
            return "ok"
        except Exception as exc:  # noqa: BLE001 - se inspecciona el mensaje de SQL Server
            texto = str(exc)
            if "50034" in texto:
                return "sin_stock"
            return f"error:{texto}"

    with ThreadPoolExecutor(max_workers=8) as executor:
        resultados = list(executor.map(intentar_salida, range(20)))

    exitos = resultados.count("ok")
    rechazos = resultados.count("sin_stock")

    assert exitos == 10, resultados
    assert rechazos == 10, resultados
    assert not [r for r in resultados if r.startswith("error:")], resultados

    actual = client.get(f"/api/productos/{producto_id}", headers=auth).json()
    assert actual["stock"] == 0
    assert actual["stock"] >= 0

    historial = client.get(
        "/api/movimientos",
        params={"producto_id": producto_id, "tamano_pagina": 100},
        headers=auth,
    ).json()

    assert historial["total"] == 11  # 1 entrada + 10 salidas confirmadas
    salidas = [item for item in historial["items"] if item["tipo"] == "SALIDA"]
    assert len(salidas) == 10
    assert all(item["stock_posterior"] >= 0 for item in salidas)

    # La cadena de stocks de las salidas encaja: 9,8,...,0 sin negativos.
    stocks = sorted(item["stock_posterior"] for item in salidas)
    assert stocks == list(range(0, 10))
