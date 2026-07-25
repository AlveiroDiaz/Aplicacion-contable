"""
Reglas de negocio de contabilización que dependen de estado en base de datos:
cuentas activas, período abierto, generación de consecutivo y persistencia
correcta de cada campo de la línea (incluyendo tercero_id, que fue un bug
real detectado y corregido en este proyecto).
"""
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.models.comprobante import Comprobante
from app.models.tercero import Tercero
from app.schemas.comprobante import ComprobanteCreate, MovimientoCreate
from app.services.comprobante_service import contabilizar_comprobante


def _comprobante_valido(empresa_id, fecha="2025-01-15", tercero_id=None):
    return ComprobanteCreate(
        empresa_id=empresa_id,
        fecha=fecha,
        descripcion="Compra de insumos",
        movimientos=[
            MovimientoCreate(cuenta_codigo="5135", debito=Decimal("1000000"), credito=Decimal("0"), tercero_id=tercero_id),
            MovimientoCreate(cuenta_codigo="2408", debito=Decimal("190000"), credito=Decimal("0")),
            MovimientoCreate(cuenta_codigo="2205", debito=Decimal("0"), credito=Decimal("1190000")),
        ],
    )


def test_contabilizar_genera_consecutivo_y_guarda_los_movimientos(db, empresa, periodo_abierto, plan_cuentas):
    comprobante = contabilizar_comprobante(db, _comprobante_valido(empresa.id))
    db.flush()

    assert comprobante.estado == "CONTABILIZADO"
    assert comprobante.consecutivo == f"COMP-{periodo_abierto.anio}{periodo_abierto.mes:02d}-00001"
    assert len(comprobante.movimientos) == 3
    assert sum(m.debito for m in comprobante.movimientos) == sum(m.credito for m in comprobante.movimientos)


def test_contabilizar_guarda_el_tercero_id_del_movimiento(db, empresa, periodo_abierto, plan_cuentas):
    tercero = Tercero(num_doc="123456789", nombre="Proveedor de prueba")
    db.add(tercero)
    db.flush()

    comprobante = contabilizar_comprobante(db, _comprobante_valido(empresa.id, tercero_id=tercero.id))
    db.flush()

    linea = next(m for m in comprobante.movimientos if m.cuenta_codigo == "5135")
    assert linea.tercero_id == tercero.id


def test_consecutivo_es_incremental_dentro_del_mismo_periodo(db, empresa, periodo_abierto, plan_cuentas):
    primero = contabilizar_comprobante(db, _comprobante_valido(empresa.id))
    db.flush()
    segundo = contabilizar_comprobante(db, _comprobante_valido(empresa.id))
    db.flush()

    assert primero.consecutivo.endswith("-00001")
    assert segundo.consecutivo.endswith("-00002")


def test_rechaza_cuenta_inactiva(db, empresa, periodo_abierto, plan_cuentas):
    comprobante_in = ComprobanteCreate(
        empresa_id=empresa.id,
        fecha="2025-01-15",
        descripcion="Usa una cuenta inactiva",
        movimientos=[
            MovimientoCreate(cuenta_codigo="5199", debito=Decimal("100"), credito=Decimal("0")),
            MovimientoCreate(cuenta_codigo="2205", debito=Decimal("0"), credito=Decimal("100")),
        ],
    )
    with pytest.raises(HTTPException) as exc:
        contabilizar_comprobante(db, comprobante_in)
    assert exc.value.status_code == 400
    assert "inactiva" in exc.value.detail.lower()


def test_rechaza_cuenta_que_no_existe(db, empresa, periodo_abierto, plan_cuentas):
    comprobante_in = ComprobanteCreate(
        empresa_id=empresa.id,
        fecha="2025-01-15",
        descripcion="Cuenta inexistente",
        movimientos=[
            MovimientoCreate(cuenta_codigo="9999-NO-EXISTE", debito=Decimal("100"), credito=Decimal("0")),
            MovimientoCreate(cuenta_codigo="2205", debito=Decimal("0"), credito=Decimal("100")),
        ],
    )
    with pytest.raises(HTTPException) as exc:
        contabilizar_comprobante(db, comprobante_in)
    assert exc.value.status_code == 400


def test_rechaza_periodo_cerrado(db, empresa, periodo_abierto, plan_cuentas):
    periodo_abierto.cerrado = True
    db.flush()

    with pytest.raises(HTTPException) as exc:
        contabilizar_comprobante(db, _comprobante_valido(empresa.id))
    assert exc.value.status_code == 400
    assert "cerrado" in exc.value.detail.lower()


def test_rechaza_periodo_inexistente_para_la_fecha(db, empresa):
    with pytest.raises(HTTPException) as exc:
        contabilizar_comprobante(db, _comprobante_valido(empresa.id, fecha="2030-05-01"))
    assert exc.value.status_code == 400


def test_precision_monetaria_se_preserva_como_decimal_en_bd(db, empresa, periodo_abierto, plan_cuentas):
    # Escenario 5: los valores no deben sufrir errores de representación
    # en punto flotante en ninguna capa (aquí: persistencia + lectura).
    comprobante = contabilizar_comprobante(db, _comprobante_valido(empresa.id))
    db.flush()
    db.expire_all()

    recargado = db.query(Comprobante).filter(Comprobante.id == comprobante.id).one()
    valores = {m.cuenta_codigo: (m.debito or m.credito) for m in recargado.movimientos}

    assert valores["2408"] == Decimal("190000.00")
    assert isinstance(valores["2408"], Decimal)
