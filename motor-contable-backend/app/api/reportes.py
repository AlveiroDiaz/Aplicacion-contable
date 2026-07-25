from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.models.comprobante import MovimientoContable, Comprobante
from app.models.cuenta import PlanCuentas # Asumiendo tu modelo de cuentas
from pydantic import BaseModel


def _tercero_display(tercero) -> Optional[str]:
    if not tercero:
        return None
    return tercero.nombre or tercero.num_doc or str(tercero.id)

router = APIRouter(tags=["Reportes Contables"])

class MovimientoLibroMayorResponse(BaseModel):
    fecha: str
    comprobante_consecutivo: str
    descripcion_comprobante: str
    descripcion_movimiento: Optional[str]
    tercero: Optional[str]
    # Decimal, no float: los montos no deben pasar por punto flotante en
    # ninguna capa (Escenario 5). Pydantic serializa Decimal a JSON
    # preservando los dígitos exactos, sin el redondeo binario de float().
    debito: Decimal
    credito: Decimal
    saldo_acumulado: Decimal

    class Config:
        from_attributes = True

class LibroMayorResponse(BaseModel):
    cuenta_codigo: str
    cuenta_nombre: str
    total_debito: Decimal
    total_credito: Decimal
    saldo_final: Decimal
    movimientos: List[MovimientoLibroMayorResponse]

@router.get("/libro-mayor", response_model=LibroMayorResponse)
def consultar_libro_mayor(
    empresa_id: UUID,
    cuenta_codigo: str,
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    # 1. Validar que la cuenta exista para la empresa
    cuenta = db.query(PlanCuentas).filter(
        PlanCuentas.codigo == cuenta_codigo,
        PlanCuentas.empresa_id == empresa_id
    ).first()
    
    if not cuenta:
        raise HTTPException(status_code=404, detail="La cuenta contable no existe.")

    # 2. Consultar los movimientos asociados a esta cuenta uniendo con la tabla comprobantes
    query = db.query(MovimientoContable, Comprobante).join(
        Comprobante, MovimientoContable.comprobante_id == Comprobante.id
    ).options(
        joinedload(MovimientoContable.tercero)
    ).filter(
        Comprobante.empresa_id == empresa_id,
        MovimientoContable.cuenta_codigo == cuenta_codigo
    )

    if fecha_inicio:
        query = query.filter(Comprobante.fecha >= fecha_inicio)
    if fecha_fin:
        query = query.filter(Comprobante.fecha <= fecha_fin)

    resultados = query.order_by(Comprobante.fecha, Comprobante.consecutivo).all()

    movimientos_lista = []
    t_debito = Decimal("0.00")
    t_credito = Decimal("0.00")
    saldo_corriendo = Decimal("0.00")

    for mov, comp in resultados:
        debito = mov.debito or Decimal("0.00")
        credito = mov.credito or Decimal("0.00")
        t_debito += debito
        t_credito += credito
        saldo_corriendo += debito - credito

        movimientos_lista.append(
            MovimientoLibroMayorResponse(
                fecha=str(comp.fecha),
                comprobante_consecutivo=comp.consecutivo,
                descripcion_comprobante=comp.descripcion,
                descripcion_movimiento=mov.descripcion,
                tercero=_tercero_display(mov.tercero),
                debito=debito,
                credito=credito,
                saldo_acumulado=saldo_corriendo
            )
        )

    saldo_final = saldo_corriendo

    return LibroMayorResponse(
        cuenta_codigo=cuenta.codigo,
        cuenta_nombre=cuenta.nombre,
        total_debito=t_debito,
        total_credito=t_credito,
        saldo_final=saldo_final,
        movimientos=movimientos_lista
    )