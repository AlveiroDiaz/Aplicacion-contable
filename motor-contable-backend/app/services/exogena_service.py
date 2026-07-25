import logging
from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Optional
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString
import re

logger = logging.getLogger(__name__)

UVT_REQUIRED_FIELDS = ["valor_uvt", "uvt", "valor"]


def calcular_dv_nit(nit: str) -> str:
    if not nit:
        raise ValueError("NIT inválido")

    raw = str(nit).strip()
    if "-" in raw:
        raw, dv_part = raw.split("-", 1)
        raw = raw.strip()
    else:
        dv_part = None

    sanitized = re.sub(r"\D", "", raw)
    if not sanitized:
        raise ValueError("NIT inválido")

    factors = [71, 67, 59, 53, 47, 43, 41, 37, 29, 23, 19, 17, 13, 7, 3]
    reversed_digits = list(map(int, sanitized[::-1]))
    total = 0
    for idx, digit in enumerate(reversed_digits):
        if idx >= len(factors):
            break
        total += digit * factors[idx]

    remainder = total % 11
    if remainder > 1:
        dv = 11 - remainder
    else:
        dv = remainder
    return str(dv)


def validar_nit_con_dv(nit: str, dv: Optional[str] = None) -> bool:
    try:
        raw = str(nit).strip()
        if "-" in raw:
            raw_nit, raw_dv = raw.split("-", 1)
            dv = raw_dv.strip()
            nit = raw_nit.strip()

        if dv is None:
            raise ValueError("Dígito de verificación no especificado")
        return calcular_dv_nit(nit) == str(dv)
    except Exception:
        return False


def format_decimal(value: Decimal) -> str:
    if value is None:
        return "0.00"
    value = Decimal(value)
    return f"{value.quantize(Decimal('0.01'))}"


def agrupar_movimientos_por_tercero_concepto(movimientos):
    agrupados = defaultdict(lambda: {"valor_bruto": Decimal("0.00"), "valor_retencion": Decimal("0.00"), "tipo_doc": "NI", "num_doc": None, "nombre": None, "concepto": None})

    for mov, comprobante in movimientos:
        if not mov.tercero_id:
            continue

        tipo_doc = getattr(getattr(mov, "tercero", None), "tipo_doc", None) or "NI"
        num_doc = getattr(getattr(mov, "tercero", None), "num_doc", None) or str(mov.tercero_id)
        nombre = getattr(getattr(mov, "tercero", None), "nombre", None) or "Tercero desconocido"
        concepto = (mov.descripcion or comprobante.descripcion or "Sin concepto").strip()

        key = (tipo_doc, num_doc, nombre, concepto)
        valor = mov.debito if mov.debito else mov.credito
        valor = Decimal(valor or 0)
        agrupados[key]["valor_bruto"] += valor
        agrupados[key]["valor_retencion"] += Decimal("0.00")
        agrupados[key]["tipo_doc"] = tipo_doc
        agrupados[key]["num_doc"] = num_doc
        agrupados[key]["nombre"] = nombre
        agrupados[key]["concepto"] = concepto

    return agrupados


def filtrar_registros_por_umbral(agrupados, umbral_pesos: Decimal):
    registros = []
    excluidos = []

    for (tipo_doc, num_doc, nombre, concepto), data in agrupados.items():
        bruto = data["valor_bruto"]
        reten = data["valor_retencion"]
        if bruto < umbral_pesos:
            excluidos.append({
                "tipo_doc": tipo_doc,
                "num_doc": num_doc,
                "nombre": nombre,
                "concepto": concepto,
                "valor_bruto": bruto,
                "valor_retencion": reten,
                "umbral": umbral_pesos,
            })
            logger.info("Excluyendo tercero %s por umbral en pesos %s", num_doc, umbral_pesos)
            continue

        registros.append({
            "tipo_doc": tipo_doc,
            "num_doc": num_doc,
            "nombre": nombre,
            "concepto": concepto,
            "valor_bruto": bruto,
            "valor_retencion": reten,
        })

    return registros, excluidos


def build_exogena_xml(empresa, anio_gravable: int, registros, total_valor_bruto: Decimal, total_retencion: Decimal):
    root = Element("InformacionExogena", version="1.0")
    SubElement(
        root,
        "Informante",
        nit=str(empresa.nit),
        dv=calcular_dv_nit(str(empresa.nit)),
        razonSocial=empresa.razon_social,
        anioGravable=str(anio_gravable),
    )

    registros_el = SubElement(root, "Registros")
    for registro in registros:
        SubElement(
            registros_el,
            "Registro",
            tipoDoc=registro["tipo_doc"],
            numDoc=registro["num_doc"],
            nombre=registro["nombre"],
            concepto=registro["concepto"],
            valorBruto=format_decimal(registro["valor_bruto"]),
            valorRetencion=format_decimal(registro["valor_retencion"]),
        )

    SubElement(
        root,
        "Totales",
        registros=str(len(registros)),
        totalValorBruto=format_decimal(total_valor_bruto),
        totalRetencion=format_decimal(total_retencion),
    )

    xml_raw = tostring(root, encoding="utf-8")
    pretty_xml = parseString(xml_raw).toprettyxml(indent="  ", encoding="utf-8")
    return pretty_xml.decode("utf-8")


def construir_parametros(a: int, umbral_uvt: int, valor_uvt: Decimal, fecha_inicio: date | None, fecha_fin: date | None) -> dict:
    return {
        "anio_gravable": a,
        "umbral_uvt": umbral_uvt,
        "valor_uvt": format_decimal(valor_uvt),
        "fecha_inicio": fecha_inicio.isoformat() if fecha_inicio else None,
        "fecha_fin": fecha_fin.isoformat() if fecha_fin else None,
    }
