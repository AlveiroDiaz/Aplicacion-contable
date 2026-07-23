from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.models.comprobante import MovimientoContable, Comprobante
from app.models.cuenta import PlanCuentas # Asumiendo tu modelo de cuentas
from pydantic import BaseModel

router = APIRouter(tags=["Reportes Contables"])

class MovimientoLibroMayorResponse(BaseModel):
    fecha: str
    comprobante_consecutivo: str
    descripcion_comprobante: str
    descripcion_movimiento: Optional[str]
    debito: float
    credito: float

    class Config:
        from_attributes = True

class LibroMayorResponse(BaseModel):
    cuenta_codigo: str
    cuenta_nombre: str
    total_debito: float
    total_credito: float
    saldo_final: float
    movimientos: List[MovimientoLibroMayorResponse]

@router.get("/libro-mayor", response_model=LibroMayorResponse)
def consultar_libro_mayor(
    empresa_id: UUID,
    cuenta_codigo: str,
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
    resultados = db.query(MovimientoContable, Comprobante).join(
        Comprobante, MovimientoContable.comprobante_id == Comprobante.id
    ).filter(
        Comprobante.empresa_id == empresa_id,
        MovimientoContable.cuenta_codigo == cuenta_codigo
    ).all()

    movimientos_lista = []
    t_debito = 0.0
    t_credito = 0.0

    for mov, comp in resultados:
        t_debito += float(mov.debito)
        t_credito += float(mov.credito)
        
        movimientos_lista.append(
            MovimientoLibroMayorResponse(
                fecha=str(comp.fecha),
                comprobante_consecutivo=comp.consecutivo,
                descripcion_comprobante=comp.descripcion,
                descripcion_movimiento=mov.descripcion,
                debito=float(mov.debito),
                credito=float(mov.credito)
            )
        )

    # 3. Calcular saldo (para cuentas de Activo/Gasto el saldo es Débito - Crédito; para Pasivo/Patrimonio/Ingreso suele ser al revés. Por simplicidad base, usaremos Débito - Crédito)
    saldo_final = t_debito - t_credito

    return LibroMayorResponse(
        cuenta_codigo=cuenta.codigo,
        cuenta_nombre=cuenta.nombre,
        total_debito=t_debito,
        total_credito=t_credito,
        saldo_final=saldo_final,
        movimientos=movimientos_lista
    )