"""
Flujo completo de 'guardar borrador' a través del API (POST /comprobantes/borrador,
PUT /{id}/borrador, POST /{id}/contabilizar), para probar el wiring de los
routers y no solo la capa de servicio.
"""


def test_flujo_completo_guardar_editar_y_contabilizar_borrador(client, empresa, periodo_abierto, plan_cuentas):
    crear = client.post(
        "/api/comprobantes/borrador",
        json={
            "empresa_id": str(empresa.id),
            "fecha": "2025-01-15",
            "descripcion": "Compra en progreso",
            "movimientos": [
                {"cuenta_codigo": "5135", "debito": "1000000", "credito": "0"},
            ],
        },
    )
    assert crear.status_code == 200
    borrador = crear.json()
    assert borrador["estado"] == "BORRADOR"
    assert borrador["consecutivo"] is None

    editar = client.put(
        f"/api/comprobantes/{borrador['id']}/borrador",
        json={
            "empresa_id": str(empresa.id),
            "fecha": "2025-01-15",
            "descripcion": "Compra de insumos completa",
            "movimientos": [
                {"cuenta_codigo": "5135", "debito": "1000000", "credito": "0"},
                {"cuenta_codigo": "2408", "debito": "190000", "credito": "0"},
                {"cuenta_codigo": "2205", "debito": "0", "credito": "1190000"},
            ],
        },
    )
    assert editar.status_code == 200
    assert len(editar.json()["movimientos"]) == 3

    contabilizar = client.post(f"/api/comprobantes/{borrador['id']}/contabilizar")
    assert contabilizar.status_code == 200
    assert contabilizar.json()["consecutivo"] is not None

    consultar = client.get(f"/api/comprobantes/{borrador['id']}")
    assert consultar.status_code == 200
    assert consultar.json()["estado"] == "CONTABILIZADO"


def test_contabilizar_borrador_desbalanceado_via_api_da_400(client, empresa, periodo_abierto, plan_cuentas):
    crear = client.post(
        "/api/comprobantes/borrador",
        json={
            "empresa_id": str(empresa.id),
            "fecha": "2025-01-15",
            "descripcion": "Desbalanceado",
            "movimientos": [
                {"cuenta_codigo": "1105", "debito": "500000", "credito": "0"},
                {"cuenta_codigo": "4135", "debito": "0", "credito": "450000"},
            ],
        },
    )
    borrador_id = crear.json()["id"]

    respuesta = client.post(f"/api/comprobantes/{borrador_id}/contabilizar")

    assert respuesta.status_code == 400
    assert "desbalanceado" in respuesta.json()["detail"].lower()


def test_no_se_puede_editar_via_api_un_comprobante_ya_contabilizado(client, empresa, periodo_abierto, plan_cuentas):
    directo = client.post(
        "/api/comprobantes/contabilizar",
        json={
            "empresa_id": str(empresa.id),
            "fecha": "2025-01-15",
            "descripcion": "Directo",
            "movimientos": [
                {"cuenta_codigo": "5135", "debito": "100", "credito": "0"},
                {"cuenta_codigo": "2205", "debito": "0", "credito": "100"},
            ],
        },
    )
    comprobante_id = directo.json()["id"]

    respuesta = client.put(
        f"/api/comprobantes/{comprobante_id}/borrador",
        json={
            "empresa_id": str(empresa.id),
            "fecha": "2025-01-15",
            "descripcion": "Intento de editar algo ya contabilizado",
            "movimientos": [],
        },
    )

    assert respuesta.status_code == 400
