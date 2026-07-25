"""
Reglas de validación que viven en el schema de Pydantic (ComprobanteCreate /
MovimientoCreate). Se prueban aisladas de la base de datos porque son puro
cálculo y son las reglas de mayor riesgo del dominio: si fallan, se puede
contabilizar una partida inconsistente.
"""
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.comprobante import ComprobanteCreate, MovimientoCreate


def _linea(**overrides):
    base = dict(cuenta_codigo="5135", debito=Decimal("0"), credito=Decimal("0"), descripcion=None)
    base.update(overrides)
    return base


def test_linea_no_admite_debito_y_credito_simultaneos():
    with pytest.raises(ValidationError):
        MovimientoCreate(**_linea(debito=Decimal("100"), credito=Decimal("100")))


def test_linea_requiere_algun_valor_distinto_de_cero():
    with pytest.raises(ValidationError):
        MovimientoCreate(**_linea())


def test_linea_no_admite_valores_negativos():
    with pytest.raises(ValidationError):
        MovimientoCreate(**_linea(debito=Decimal("-1")))


def test_comprobante_requiere_minimo_dos_lineas():
    with pytest.raises(ValidationError):
        ComprobanteCreate(
            empresa_id=uuid4(),
            fecha="2025-01-15",
            descripcion="Test",
            movimientos=[MovimientoCreate(**_linea(debito=Decimal("100")))],
        )


def test_comprobante_balanceado_es_aceptado():
    # Escenario 1 del enunciado: compra con IVA descontable.
    comprobante = ComprobanteCreate(
        empresa_id=uuid4(),
        fecha="2025-01-15",
        descripcion="Compra de insumos",
        movimientos=[
            MovimientoCreate(**_linea(cuenta_codigo="5135", debito=Decimal("1000000"))),
            MovimientoCreate(**_linea(cuenta_codigo="2408", debito=Decimal("190000"))),
            MovimientoCreate(**_linea(cuenta_codigo="2205", credito=Decimal("1190000"))),
        ],
    )
    assert len(comprobante.movimientos) == 3


def test_comprobante_desbalanceado_es_rechazado():
    # Escenario 2 del enunciado: caja vs. ingresos sin cuadrar.
    with pytest.raises(ValidationError) as exc:
        ComprobanteCreate(
            empresa_id=uuid4(),
            fecha="2025-01-15",
            descripcion="Comprobante desbalanceado",
            movimientos=[
                MovimientoCreate(**_linea(cuenta_codigo="1105", debito=Decimal("500000"))),
                MovimientoCreate(**_linea(cuenta_codigo="4135", credito=Decimal("450000"))),
            ],
        )
    assert "desbalanceado" in str(exc.value).lower()
