"""
Login JWT (extensión opcional de la sección 11). A diferencia del resto de
la suite, estos tests usan un TestClient SIN el override de
obtener_usuario_actual (ver fixture `client` en conftest.py), justamente
para verificar el flujo real de punta a punta: login correcto/incorrecto,
que el resto del API exige el token, y que un token vencido se rechaza.
"""
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.core.config import settings
from app.core.database import get_db
from app.core.security import hash_password
from app.main import app
from app.models.usuario import Usuario


@pytest.fixture()
def client_con_auth_real(db):
    """Igual que el fixture `client`, pero deliberadamente NO sobreescribe
    obtener_usuario_actual: solo bypassea la base de datos, para poder
    probar el login y la protección de rutas tal como funcionan de verdad."""
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
def usuario_prueba(db):
    usuario = Usuario(username="carlos", password_hash=hash_password("clave-segura-123"), nombre="Carlos", activo=True)
    db.add(usuario)
    db.flush()
    return usuario


def test_login_con_credenciales_correctas_devuelve_token(client_con_auth_real, usuario_prueba):
    respuesta = client_con_auth_real.post("/api/auth/login", json={"username": "carlos", "password": "clave-segura-123"})

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["access_token"]
    assert cuerpo["token_type"] == "bearer"
    assert cuerpo["usuario"]["username"] == "carlos"


def test_login_con_password_incorrecta_es_rechazado(client_con_auth_real, usuario_prueba):
    respuesta = client_con_auth_real.post("/api/auth/login", json={"username": "carlos", "password": "incorrecta"})
    assert respuesta.status_code == 401


def test_login_con_usuario_inexistente_es_rechazado(client_con_auth_real):
    respuesta = client_con_auth_real.post("/api/auth/login", json={"username": "no-existe", "password": "x"})
    assert respuesta.status_code == 401


def test_login_de_usuario_inactivo_es_rechazado(client_con_auth_real, db):
    usuario = Usuario(username="inactivo", password_hash=hash_password("clave123"), activo=False)
    db.add(usuario)
    db.flush()

    respuesta = client_con_auth_real.post("/api/auth/login", json={"username": "inactivo", "password": "clave123"})
    assert respuesta.status_code == 401


def test_endpoint_protegido_sin_token_es_rechazado(client_con_auth_real):
    respuesta = client_con_auth_real.get("/api/empresas/")
    assert respuesta.status_code == 401


def test_endpoint_protegido_con_token_valido_responde(client_con_auth_real, usuario_prueba):
    login = client_con_auth_real.post("/api/auth/login", json={"username": "carlos", "password": "clave-segura-123"})
    token = login.json()["access_token"]

    respuesta = client_con_auth_real.get("/api/empresas/", headers={"Authorization": f"Bearer {token}"})
    assert respuesta.status_code == 200


def test_endpoint_protegido_con_token_expirado_es_rechazado(client_con_auth_real, usuario_prueba):
    payload = {
        "sub": str(usuario_prueba.id),
        "username": usuario_prueba.username,
        "iat": datetime.now(timezone.utc) - timedelta(hours=2),
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
    }
    token_vencido = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    respuesta = client_con_auth_real.get("/api/empresas/", headers={"Authorization": f"Bearer {token_vencido}"})
    assert respuesta.status_code == 401


def test_endpoint_protegido_con_token_firmado_con_otra_clave_es_rechazado(client_con_auth_real, usuario_prueba):
    payload = {
        "sub": str(usuario_prueba.id),
        "username": usuario_prueba.username,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    token_falso = jwt.encode(payload, "otra-clave-cualquiera", algorithm=settings.JWT_ALGORITHM)

    respuesta = client_con_auth_real.get("/api/empresas/", headers={"Authorization": f"Bearer {token_falso}"})
    assert respuesta.status_code == 401


def test_login_del_admin_sembrado_por_defecto(client_con_auth_real):
    # app/core/seed.py crea admin/admin123 al arrancar la app si no existe
    # ningún usuario con ese username; se verifica que de verdad funciona.
    respuesta = client_con_auth_real.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert respuesta.status_code == 200


def test_endpoint_login_no_requiere_token(client_con_auth_real):
    # /api/auth/login es la única ruta pública: no debe exigir Authorization.
    # Si la exigiera, el detail sería "No autenticado." en vez del mensaje
    # de credenciales inválidas propio del endpoint de login.
    respuesta = client_con_auth_real.post("/api/auth/login", json={"username": "quien-sea", "password": "x"})
    assert respuesta.status_code == 401
    assert respuesta.json()["detail"] == "Usuario o contraseña incorrectos."
