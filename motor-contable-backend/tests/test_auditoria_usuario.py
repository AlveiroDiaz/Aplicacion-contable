"""
Atribución de usuario en el ciclo de vida del comprobante (regla 9.3:
"las operaciones relevantes ... deben ser auditables"). Se prueba a nivel
de API con un login real (no con el fixture `client`, que bypassea la
autenticación) para verificar que el usuario que efectivamente quedó
grabado es el que se autenticó con el JWT, no un valor arbitrario.
"""
from decimal import Decimal

import pytest

from app.core.database import get_db
from app.core.security import hash_password
from app.main import app
from app.models.usuario import Usuario


@pytest.fixture()
def client_real_auth(db):
    from fastapi.testclient import TestClient

    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
def sesion_autenticada(client_real_auth, db):
    usuario = Usuario(username="ana.contadora", password_hash=hash_password("clave-segura-123"), nombre="Ana Contadora", activo=True)
    db.add(usuario)
    db.flush()

    login = client_real_auth.post("/api/auth/login", json={"username": "ana.contadora", "password": "clave-segura-123"})
    assert login.status_code == 200
    token = login.json()["access_token"]

    return client_real_auth, usuario, {"Authorization": f"Bearer {token}"}


def _movimientos_balanceados():
    return [
        {"cuenta_codigo": "5135", "debito": "100", "credito": "0"},
        {"cuenta_codigo": "2205", "debito": "0", "credito": "100"},
    ]


def test_contabilizar_directo_registra_quien_creo_y_contabilizo(sesion_autenticada, empresa, periodo_abierto, plan_cuentas):
    client, usuario, headers = sesion_autenticada

    respuesta = client.post(
        "/api/comprobantes/contabilizar",
        json={
            "empresa_id": str(empresa.id),
            "fecha": "2025-01-15",
            "descripcion": "Compra",
            "movimientos": _movimientos_balanceados(),
        },
        headers=headers,
    )
    assert respuesta.status_code == 200
    comprobante_id = respuesta.json()["id"]

    detalle = client.get(f"/api/comprobantes/{comprobante_id}", headers=headers).json()
    assert detalle["creado_por_id"] == str(usuario.id)
    assert detalle["contabilizado_por_id"] == str(usuario.id)
    assert detalle["contabilizado_en"] is not None


def test_guardar_borrador_registra_quien_lo_creo_sin_contabilizar(sesion_autenticada, empresa, periodo_abierto, plan_cuentas):
    client, usuario, headers = sesion_autenticada

    respuesta = client.post(
        "/api/comprobantes/borrador",
        json={
            "empresa_id": str(empresa.id),
            "fecha": "2025-01-15",
            "descripcion": "Borrador en progreso",
            "movimientos": [{"cuenta_codigo": "5135", "debito": "100", "credito": "0"}],
        },
        headers=headers,
    )
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["creado_por_id"] == str(usuario.id)
    assert cuerpo["contabilizado_por_id"] is None


def test_contabilizar_borrador_registra_quien_lo_contabilizo(sesion_autenticada, empresa, periodo_abierto, plan_cuentas):
    client, usuario, headers = sesion_autenticada

    borrador = client.post(
        "/api/comprobantes/borrador",
        json={
            "empresa_id": str(empresa.id),
            "fecha": "2025-01-15",
            "descripcion": "Compra",
            "movimientos": _movimientos_balanceados(),
        },
        headers=headers,
    ).json()

    client.post(f"/api/comprobantes/{borrador['id']}/contabilizar", headers=headers)

    detalle = client.get(f"/api/comprobantes/{borrador['id']}", headers=headers).json()
    assert detalle["contabilizado_por_id"] == str(usuario.id)
    assert detalle["contabilizado_en"] is not None


def test_revertir_registra_quien_revirtio_y_quien_creo_la_reversion(sesion_autenticada, empresa, periodo_abierto, plan_cuentas):
    client, usuario, headers = sesion_autenticada

    original = client.post(
        "/api/comprobantes/contabilizar",
        json={
            "empresa_id": str(empresa.id),
            "fecha": "2025-01-15",
            "descripcion": "Compra",
            "movimientos": _movimientos_balanceados(),
        },
        headers=headers,
    ).json()

    reversion = client.post(f"/api/comprobantes/{original['id']}/revertir", headers=headers)
    assert reversion.status_code == 200
    nuevo_id = reversion.json()["comprobante_nuevo_id"]

    original_detalle = client.get(f"/api/comprobantes/{original['id']}", headers=headers).json()
    assert original_detalle["revertido_por_id"] == str(usuario.id)
    assert original_detalle["revertido_en"] is not None

    reversion_detalle = client.get(f"/api/comprobantes/{nuevo_id}", headers=headers).json()
    assert reversion_detalle["creado_por_id"] == str(usuario.id)
    assert reversion_detalle["contabilizado_por_id"] == str(usuario.id)
