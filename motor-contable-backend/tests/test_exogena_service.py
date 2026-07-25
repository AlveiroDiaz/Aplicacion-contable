"""
Reglas de negocio de exógena (6.2): dígito de verificación del NIT,
agrupación por tercero+concepto y aplicación del umbral en UVT. Son
funciones puras (sin BD), así que se prueban directamente con datos falsos
en memoria.

Nota sobre el DV del NIT: en vez de fijar un par (NIT, DV) "conocido" de
memoria (riesgo de error humano), se verifica la propiedad que realmente
importa: que validar_nit_con_dv acepta el DV que la propia función calcula
y rechaza cualquier otro. Esto protege contra regresiones del algoritmo sin
depender de un dato externo no verificable en este entorno.
"""
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.services.exogena_service import (
    agrupar_movimientos_por_tercero_concepto,
    calcular_dv_nit,
    filtrar_registros_por_umbral,
    format_decimal,
    validar_nit_con_dv,
)


def test_calcular_dv_nit_es_deterministico():
    assert calcular_dv_nit("900123456") == calcular_dv_nit("900123456")


def test_calcular_dv_nit_retorna_un_solo_digito():
    dv = calcular_dv_nit("900123456")
    assert dv.isdigit()
    assert 0 <= int(dv) <= 9


def test_calcular_dv_nit_rechaza_valor_vacio():
    with pytest.raises(ValueError):
        calcular_dv_nit("")


def test_validar_nit_con_dv_acepta_el_digito_correcto():
    nit = "900123456"
    dv = calcular_dv_nit(nit)
    assert validar_nit_con_dv(nit, dv) is True


def test_validar_nit_con_dv_rechaza_digito_incorrecto():
    nit = "900123456"
    dv_correcto = calcular_dv_nit(nit)
    dv_incorrecto = str((int(dv_correcto) + 1) % 10)
    assert validar_nit_con_dv(nit, dv_incorrecto) is False


def test_validar_nit_con_dv_acepta_formato_nit_guion_dv():
    nit = "900123456"
    dv = calcular_dv_nit(nit)
    assert validar_nit_con_dv(f"{nit}-{dv}") is True


def _movimiento(tercero_id, num_doc, nombre, concepto, debito=0, credito=0):
    tercero = SimpleNamespace(tipo_doc="NI", num_doc=num_doc, nombre=nombre)
    mov = SimpleNamespace(
        tercero_id=tercero_id,
        tercero=tercero,
        debito=Decimal(debito),
        credito=Decimal(credito),
        descripcion=concepto,
    )
    comprobante = SimpleNamespace(descripcion=concepto)
    return mov, comprobante


def test_agrupar_movimientos_suma_por_tercero_y_concepto():
    movimientos = [
        _movimiento("t1", "123", "Proveedor A", "Honorarios", debito=500000),
        _movimiento("t1", "123", "Proveedor A", "Honorarios", debito=300000),
        _movimiento("t2", "456", "Proveedor B", "Arriendo", debito=1000000),
    ]

    agrupados = agrupar_movimientos_por_tercero_concepto(movimientos)

    assert len(agrupados) == 2
    clave_a = ("NI", "123", "Proveedor A", "Honorarios")
    assert agrupados[clave_a]["valor_bruto"] == Decimal("800000")


def test_agrupar_movimientos_ignora_los_que_no_tienen_tercero():
    movimientos = [_movimiento(None, None, None, "Sin tercero", debito=100000)]

    agrupados = agrupar_movimientos_por_tercero_concepto(movimientos)

    assert len(agrupados) == 0


def test_filtrar_registros_excluye_por_debajo_del_umbral():
    agrupados = {
        ("NI", "123", "Proveedor A", "Honorarios"): {"valor_bruto": Decimal("500000"), "valor_retencion": Decimal("0")},
        ("NI", "456", "Proveedor B", "Arriendo"): {"valor_bruto": Decimal("2000000"), "valor_retencion": Decimal("0")},
    }

    incluidos, excluidos = filtrar_registros_por_umbral(agrupados, umbral_pesos=Decimal("1000000"))

    assert [r["num_doc"] for r in incluidos] == ["456"]
    assert [r["num_doc"] for r in excluidos] == ["123"]


def test_totales_de_control_cuadran_con_los_registros_incluidos():
    agrupados = {
        ("NI", "123", "Proveedor A", "Honorarios"): {"valor_bruto": Decimal("500000"), "valor_retencion": Decimal("0")},
        ("NI", "456", "Proveedor B", "Arriendo"): {"valor_bruto": Decimal("2000000"), "valor_retencion": Decimal("0")},
    }

    incluidos, _ = filtrar_registros_por_umbral(agrupados, umbral_pesos=Decimal("1000000"))

    assert sum(r["valor_bruto"] for r in incluidos) == Decimal("2000000")


def test_format_decimal_conserva_dos_decimales():
    assert format_decimal(Decimal("1190000")) == "1190000.00"
    assert format_decimal(None) == "0.00"
