"""
Escenario 3 del enunciado: un comprobante contabilizado con error debe poder
corregirse conservando trazabilidad completa (el original nunca se borra ni
se edita; se genera un contraasiento).
"""
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.schemas.comprobante import ComprobanteCreate, MovimientoCreate
from app.services.comprobante_service import contabilizar_comprobante, revertir_comprobante


def _comprobante_valido(empresa_id):
    return ComprobanteCreate(
        empresa_id=empresa_id,
        fecha="2025-01-15",
        descripcion="Compra de insumos",
        movimientos=[
            MovimientoCreate(cuenta_codigo="5135", debito=Decimal("1000000"), credito=Decimal("0")),
            MovimientoCreate(cuenta_codigo="2408", debito=Decimal("190000"), credito=Decimal("0")),
            MovimientoCreate(cuenta_codigo="2205", debito=Decimal("0"), credito=Decimal("1190000")),
        ],
    )


def test_revertir_genera_contraasiento_balanceado_y_marca_el_original(db, empresa, periodo_abierto, plan_cuentas):
    original = contabilizar_comprobante(db, _comprobante_valido(empresa.id))
    db.flush()

    reversion = revertir_comprobante(db, original.id)
    db.flush()

    assert original.revertido is True
    assert reversion.id != original.id
    assert reversion.estado == "CONTABILIZADO"
    assert sum(m.debito for m in reversion.movimientos) == sum(m.credito for m in reversion.movimientos)

    originales_por_cuenta = {m.cuenta_codigo: m for m in original.movimientos}
    for mov_reversion in reversion.movimientos:
        mov_original = originales_por_cuenta[mov_reversion.cuenta_codigo]
        assert mov_reversion.debito == mov_original.credito
        assert mov_reversion.credito == mov_original.debito


def test_el_original_permanece_intacto_tras_revertir(db, empresa, periodo_abierto, plan_cuentas):
    original = contabilizar_comprobante(db, _comprobante_valido(empresa.id))
    db.flush()
    total_debito_original = sum(m.debito for m in original.movimientos)

    revertir_comprobante(db, original.id)
    db.flush()

    assert sum(m.debito for m in original.movimientos) == total_debito_original
    assert len(original.movimientos) == 3


def test_no_permite_revertir_un_comprobante_dos_veces(db, empresa, periodo_abierto, plan_cuentas):
    original = contabilizar_comprobante(db, _comprobante_valido(empresa.id))
    db.flush()
    revertir_comprobante(db, original.id)
    db.flush()

    with pytest.raises(HTTPException) as exc:
        revertir_comprobante(db, original.id)
    assert exc.value.status_code == 400


def test_no_permite_revertir_en_un_periodo_ya_cerrado(db, empresa, periodo_abierto, plan_cuentas):
    original = contabilizar_comprobante(db, _comprobante_valido(empresa.id))
    db.flush()
    periodo_abierto.cerrado = True
    db.flush()

    with pytest.raises(HTTPException) as exc:
        revertir_comprobante(db, original.id)
    assert exc.value.status_code == 400
