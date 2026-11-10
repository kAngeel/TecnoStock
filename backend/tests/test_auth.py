"""Pruebas de autenticación y estado del servicio."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_reporta_base_de_datos(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"


def test_health_responde_tambien_sin_prefijo_api(client: TestClient) -> None:
    """Alias /health para sondas de disponibilidad que no usan /api."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == client.get("/api/health").json()


def test_login_correcto_entrega_token_y_usuario(
    client: TestClient, admin_credentials: tuple[str, str]
) -> None:
    username, password = admin_credentials
    response = client.post(
        "/api/auth/login",
        json={"nombre_usuario": username, "contrasena": password},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] > 0
    assert len(body["access_token"].split(".")) == 3
    assert body["usuario"]["nombre_usuario"] == username
    assert "contrasena" not in body["usuario"]
    assert "clave_hash" not in body["usuario"]


def test_login_con_password_incorrecta_falla(
    client: TestClient, admin_credentials: tuple[str, str]
) -> None:
    username, _ = admin_credentials
    response = client.post(
        "/api/auth/login",
        json={"nombre_usuario": username, "contrasena": "ClaveEquivocada2026"},
    )

    assert response.status_code == 401
    assert response.json()["code"] == "credenciales_invalidas"
    # El mensaje no revela si el usuario existe.
    assert "incorrectos" in response.json()["detail"]


def test_login_con_usuario_inexistente_falla(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login",
        json={"nombre_usuario": "no.existe.tst", "contrasena": "Cualquiera2026"},
    )

    assert response.status_code == 401
    assert response.json()["code"] == "credenciales_invalidas"


def test_ruta_protegida_sin_token_devuelve_401(client: TestClient) -> None:
    response = client.get("/api/productos")

    assert response.status_code == 401
    assert response.json()["code"] == "token_requerido"


def test_ruta_protegida_con_token_invalido_devuelve_401(client: TestClient) -> None:
    response = client.get(
        "/api/productos", headers={"Authorization": "Bearer token.invalido.aqui"}
    )

    assert response.status_code == 401
    assert response.json()["code"] == "token_invalido"


def test_me_devuelve_el_usuario_autenticado(
    client: TestClient, auth: dict[str, str], admin_credentials: tuple[str, str]
) -> None:
    response = client.get("/api/auth/me", headers=auth)

    assert response.status_code == 200
    body = response.json()
    assert body["nombre_usuario"] == admin_credentials[0]
    assert body["activo"] is True
    assert "clave_hash" not in body


def test_validacion_de_campos_en_login(client: TestClient) -> None:
    response = client.post("/api/auth/login", json={"nombre_usuario": ""})

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "datos_invalidos"
    assert isinstance(body["details"], list) and body["details"]
