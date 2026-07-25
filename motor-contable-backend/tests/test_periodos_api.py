"""
Cierre de período (3.5) y Escenario 4. Se prueban a través del API completo
(TestClient) en vez de solo el service, porque acá el riesgo mayor era un bug
real de wiring: el endpoint bloqueaba el cierre si había comprobantes
CONTABILIZADOS (el caso normal), no solo BORRADOR. Estas pruebas fijan el
comportamiento correcto para que no vuelva a romperse.
"""
from datetime import date
from decimal import Decimal

from app.models.comprobante import Comprobante
from app.schemas.comprobante import ComprobanteCreate, MovimientoCreate
from app.services.comprobante_service import contabilizar_comprobante


def _cerrar(client, empresa, periodo):
    return client.post(
        "/api/periodos/cerrar",
        json={"empresa_id": str(empresa.id), "anio": periodo.anio, "mes": periodo.mes},
    )


def test_cierre_bloqueado_si_hay_borradores_pendientes(client, db, empresa, periodo_abierto):
    borrador = Comprobante(
        empresa_id=empresa.id,
        periodo_id=periodo_abierto.id,
        fecha=date(periodo_abierto.anio, periodo_abierto.mes, 15),
        descripcion="Borrador sin terminar",
        estado="BORRADOR",
    )
    db.add(borrador)
    db.flush()

    response = _cerrar(client, empresa, periodo_abierto)

    assert response.status_code == 400
    assert "borrador" in response.json()["detail"].lower()


def test_cierre_permitido_con_comprobantes_ya_contabilizados(client, db, empresa, periodo_abierto, plan_cuentas):
    # Regresión: antes del fix, esto se rechazaba con 400 aunque fuera el
    # flujo normal (un período se cierra DESPUÉS de contabilizar).
    contabilizar_comprobante(db, ComprobanteCreate(
        empresa_id=empresa.id,
        fecha=f"{periodo_abierto.anio}-{periodo_abierto.mes:02d}-15",
        descripcion="Asiento contabilizado",
        movimientos=[
            MovimientoCreate(cuenta_codigo="5135", debito=Decimal("100"), credito=Decimal("0")),
            MovimientoCreate(cuenta_codigo="2205", debito=Decimal("0"), credito=Decimal("100")),
        ],
    ))
    db.commit()

    response = _cerrar(client, empresa, periodo_abierto)

    assert response.status_code == 200
    assert response.json()["cerrado"] is True


def test_no_permite_cerrar_un_periodo_ya_cerrado(client, db, empresa, periodo_abierto):
    periodo_abierto.cerrado = True
    db.commit()

    response = _cerrar(client, empresa, periodo_abierto)

    assert response.status_code == 400


def test_periodo_cerrado_rechaza_nuevos_comprobantes_via_api(client, db, empresa, periodo_abierto, plan_cuentas):
    # Escenario 4: período 2025-01 cerrado, se intenta contabilizar en enero.
    periodo_abierto.cerrado = True
    db.commit()

    response = client.post(
        "/api/comprobantes/contabilizar",
        json={
            "empresa_id": str(empresa.id),
            "fecha": f"{periodo_abierto.anio}-{periodo_abierto.mes:02d}-15",
            "descripcion": "No debería contabilizarse",
            "movimientos": [
                {"cuenta_codigo": "5135", "debito": "100", "credito": "0"},
                {"cuenta_codigo": "2205", "debito": "0", "credito": "100"},
            ],
        },
    )

    assert response.status_code == 400
    assert "cerrado" in response.json()["detail"].lower()
