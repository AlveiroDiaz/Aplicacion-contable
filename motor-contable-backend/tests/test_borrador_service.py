"""
'Guardar como borrador' (Vista 1 del enunciado). Reglas de mayor riesgo:
un borrador debe poder estar incompleto o desbalanceado (a diferencia de
contabilizar_comprobante), pero nunca debe poder saltarse la validación
completa al momento de promoverlo a CONTABILIZADO, y nunca debe poder
editarse una vez contabilizado (regla 3.3.7 de protección).
"""
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.schemas.comprobante import ComprobanteBorradorCreate, MovimientoBorradorCreate
from app.services.comprobante_service import (
    actualizar_borrador,
    contabilizar_borrador,
    contabilizar_comprobante,
    crear_borrador,
)


def test_borrador_admite_una_sola_linea_y_valores_desbalanceados(db, empresa, periodo_abierto, plan_cuentas):
    borrador_in = ComprobanteBorradorCreate(
        empresa_id=empresa.id,
        fecha="2025-01-15",
        descripcion="Compra en progreso",
        movimientos=[
            MovimientoBorradorCreate(cuenta_codigo="5135", debito=Decimal("1000000"), credito=Decimal("0")),
        ],
    )

    comprobante = crear_borrador(db, borrador_in)
    db.flush()

    assert comprobante.estado == "BORRADOR"
    assert comprobante.consecutivo is None
    assert len(comprobante.movimientos) == 1


def test_borrador_admite_cero_lineas(db, empresa, periodo_abierto, plan_cuentas):
    borrador_in = ComprobanteBorradorCreate(
        empresa_id=empresa.id,
        fecha="2025-01-15",
        descripcion="Solo encabezado, todavía sin líneas",
        movimientos=[],
    )

    comprobante = crear_borrador(db, borrador_in)
    db.flush()

    assert comprobante.estado == "BORRADOR"
    assert comprobante.movimientos == []


def test_borrador_no_admite_debito_y_credito_simultaneos_en_la_misma_linea():
    with pytest.raises(Exception):
        MovimientoBorradorCreate(cuenta_codigo="5135", debito=Decimal("100"), credito=Decimal("100"))


def test_borrador_no_consume_numeracion_de_consecutivo(db, empresa, periodo_abierto, plan_cuentas):
    crear_borrador(db, ComprobanteBorradorCreate(
        empresa_id=empresa.id,
        fecha="2025-01-15",
        descripcion="Borrador 1",
        movimientos=[MovimientoBorradorCreate(cuenta_codigo="5135", debito=Decimal("100"), credito=Decimal("0"))],
    ))
    db.flush()

    from app.schemas.comprobante import ComprobanteCreate, MovimientoCreate
    contabilizado = contabilizar_comprobante(db, ComprobanteCreate(
        empresa_id=empresa.id,
        fecha="2025-01-15",
        descripcion="Comprobante real",
        movimientos=[
            MovimientoCreate(cuenta_codigo="5135", debito=Decimal("100"), credito=Decimal("0")),
            MovimientoCreate(cuenta_codigo="2205", debito=Decimal("0"), credito=Decimal("100")),
        ],
    ))
    db.flush()

    # El borrador previo no debe haber consumido el folio -00001.
    assert contabilizado.consecutivo.endswith("-00001")


def test_actualizar_borrador_reemplaza_lineas(db, empresa, periodo_abierto, plan_cuentas):
    borrador = crear_borrador(db, ComprobanteBorradorCreate(
        empresa_id=empresa.id,
        fecha="2025-01-15",
        descripcion="Versión 1",
        movimientos=[MovimientoBorradorCreate(cuenta_codigo="5135", debito=Decimal("100"), credito=Decimal("0"))],
    ))
    db.flush()

    actualizado = actualizar_borrador(db, borrador.id, ComprobanteBorradorCreate(
        empresa_id=empresa.id,
        fecha="2025-01-16",
        descripcion="Versión 2",
        movimientos=[
            MovimientoBorradorCreate(cuenta_codigo="5135", debito=Decimal("1000000"), credito=Decimal("0")),
            MovimientoBorradorCreate(cuenta_codigo="2408", debito=Decimal("190000"), credito=Decimal("0")),
            MovimientoBorradorCreate(cuenta_codigo="2205", debito=Decimal("0"), credito=Decimal("1190000")),
        ],
    ))
    db.flush()

    assert actualizado.descripcion == "Versión 2"
    assert len(actualizado.movimientos) == 3


def test_no_se_puede_editar_un_borrador_que_ya_fue_contabilizado(db, empresa, periodo_abierto, plan_cuentas):
    borrador = crear_borrador(db, ComprobanteBorradorCreate(
        empresa_id=empresa.id,
        fecha="2025-01-15",
        descripcion="Compra",
        movimientos=[
            MovimientoBorradorCreate(cuenta_codigo="5135", debito=Decimal("100"), credito=Decimal("0")),
            MovimientoBorradorCreate(cuenta_codigo="2205", debito=Decimal("0"), credito=Decimal("100")),
        ],
    ))
    db.flush()
    contabilizar_borrador(db, borrador.id)
    db.flush()

    with pytest.raises(HTTPException) as exc:
        actualizar_borrador(db, borrador.id, ComprobanteBorradorCreate(
            empresa_id=empresa.id,
            fecha="2025-01-15",
            descripcion="Intento de editar algo ya contabilizado",
            movimientos=[],
        ))
    assert exc.value.status_code == 400


def test_contabilizar_borrador_incompleto_es_rechazado_con_mensaje_claro(db, empresa, periodo_abierto, plan_cuentas):
    borrador = crear_borrador(db, ComprobanteBorradorCreate(
        empresa_id=empresa.id,
        fecha="2025-01-15",
        descripcion="Solo una línea, no cuadra",
        movimientos=[MovimientoBorradorCreate(cuenta_codigo="5135", debito=Decimal("100"), credito=Decimal("0"))],
    ))
    db.flush()

    with pytest.raises(HTTPException) as exc:
        contabilizar_borrador(db, borrador.id)
    assert exc.value.status_code == 400


def test_contabilizar_borrador_valido_asigna_consecutivo_y_cambia_estado(db, empresa, periodo_abierto, plan_cuentas):
    borrador = crear_borrador(db, ComprobanteBorradorCreate(
        empresa_id=empresa.id,
        fecha="2025-01-15",
        descripcion="Compra de insumos",
        movimientos=[
            MovimientoBorradorCreate(cuenta_codigo="5135", debito=Decimal("1000000"), credito=Decimal("0")),
            MovimientoBorradorCreate(cuenta_codigo="2408", debito=Decimal("190000"), credito=Decimal("0")),
            MovimientoBorradorCreate(cuenta_codigo="2205", debito=Decimal("0"), credito=Decimal("1190000")),
        ],
    ))
    db.flush()

    contabilizado = contabilizar_borrador(db, borrador.id)
    db.flush()

    assert contabilizado.estado == "CONTABILIZADO"
    assert contabilizado.consecutivo is not None


def test_contabilizar_borrador_rechaza_cuenta_inactiva(db, empresa, periodo_abierto, plan_cuentas):
    borrador = crear_borrador(db, ComprobanteBorradorCreate(
        empresa_id=empresa.id,
        fecha="2025-01-15",
        descripcion="Usa cuenta inactiva",
        movimientos=[
            MovimientoBorradorCreate(cuenta_codigo="5199", debito=Decimal("100"), credito=Decimal("0")),
            MovimientoBorradorCreate(cuenta_codigo="2205", debito=Decimal("0"), credito=Decimal("100")),
        ],
    ))
    db.flush()

    with pytest.raises(HTTPException) as exc:
        contabilizar_borrador(db, borrador.id)
    assert exc.value.status_code == 400
    assert "inactiva" in exc.value.detail.lower()


def test_borrador_se_puede_crear_en_periodo_cerrado_pero_no_contabilizar(db, empresa, periodo_abierto, plan_cuentas):
    periodo_abierto.cerrado = True
    db.flush()

    borrador = crear_borrador(db, ComprobanteBorradorCreate(
        empresa_id=empresa.id,
        fecha="2025-01-15",
        descripcion="Preparado para un período ya cerrado",
        movimientos=[
            MovimientoBorradorCreate(cuenta_codigo="5135", debito=Decimal("100"), credito=Decimal("0")),
            MovimientoBorradorCreate(cuenta_codigo="2205", debito=Decimal("0"), credito=Decimal("100")),
        ],
    ))
    db.flush()
    assert borrador.estado == "BORRADOR"

    with pytest.raises(HTTPException) as exc:
        contabilizar_borrador(db, borrador.id)
    assert exc.value.status_code == 400
    assert "cerrado" in exc.value.detail.lower()


def test_contabilizar_borrador_inexistente_da_404(db):
    import uuid
    with pytest.raises(HTTPException) as exc:
        contabilizar_borrador(db, uuid.uuid4())
    assert exc.value.status_code == 404
