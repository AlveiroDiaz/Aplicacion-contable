"""
Escenario 5 aplicado al libro mayor: antes, api/reportes.py convertía los
Decimal a float antes de responder. Se verifica sobre el TEXTO crudo del
JSON (no sobre el dict ya parseado por Python) porque un `.json()` habría
podido enmascarar el problema silenciosamente.
"""
from decimal import Decimal


def _contabilizar(client, empresa, fecha, movimientos):
    respuesta = client.post(
        "/api/comprobantes/contabilizar",
        json={
            "empresa_id": str(empresa.id),
            "fecha": fecha,
            "descripcion": "Movimiento de prueba",
            "movimientos": movimientos,
        },
    )
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()


def test_libro_mayor_no_pierde_precision_al_serializar(client, empresa, periodo_abierto, plan_cuentas):
    # 0.10 + 0.20 es el ejemplo clásico de error de representación en
    # punto flotante binario (0.1 + 0.2 == 0.30000000000000004 en float).
    _contabilizar(client, empresa, "2025-01-15", [
        {"cuenta_codigo": "5135", "debito": "0.10", "credito": "0.00"},
        {"cuenta_codigo": "2408", "debito": "0.20", "credito": "0.00"},
        {"cuenta_codigo": "2205", "debito": "0.00", "credito": "0.30"},
    ])

    respuesta = client.get(
        "/api/reportes/libro-mayor",
        params={"empresa_id": str(empresa.id), "cuenta_codigo": "2205"},
    )

    assert respuesta.status_code == 200
    # Se revisa el texto crudo: si algo volviera a convertir a float por el
    # camino, aparecería como "0.29999999999999999" o "0.3" en vez de
    # "0.30" exacto.
    assert '"credito":"0.30"' in respuesta.text
    assert '"saldo_acumulado":"-0.30"' in respuesta.text
    assert '"total_credito":"0.30"' in respuesta.text

    cuerpo = respuesta.json()
    assert Decimal(cuerpo["total_credito"]) == Decimal("0.30")
    assert Decimal(cuerpo["saldo_final"]) == Decimal("-0.30")


def test_libro_mayor_incluye_tercero_cuando_aplica(client, empresa, periodo_abierto, plan_cuentas, db):
    from app.models.tercero import Tercero

    tercero = Tercero(num_doc="123456789", nombre="Proveedor de prueba")
    db.add(tercero)
    db.flush()

    _contabilizar(client, empresa, "2025-01-15", [
        {"cuenta_codigo": "5135", "debito": "100000", "credito": "0", "tercero_id": str(tercero.id)},
        {"cuenta_codigo": "2205", "debito": "0", "credito": "100000"},
    ])

    respuesta = client.get(
        "/api/reportes/libro-mayor",
        params={"empresa_id": str(empresa.id), "cuenta_codigo": "5135"},
    )

    assert respuesta.status_code == 200
    movimiento = respuesta.json()["movimientos"][0]
    assert movimiento["tercero"] == str(tercero.id)
