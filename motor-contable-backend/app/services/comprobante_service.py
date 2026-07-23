from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.comprobante import Comprobante, MovimientoContable
from app.models.periodo import PeriodoContable
from app.models.cuenta import PlanCuentas
from app.schemas.comprobante import ComprobanteCreate, MovimientoCreate
from decimal import Decimal

def contabilizar_comprobante(db: Session, comprobante_in: ComprobanteCreate):
    anio = comprobante_in.fecha.year
    mes = comprobante_in.fecha.month

    periodo = db.query(PeriodoContable).filter(
        PeriodoContable.empresa_id == comprobante_in.empresa_id,
        PeriodoContable.anio == anio,
        PeriodoContable.mes == mes
    ).with_for_update().first()

    if not periodo:
        raise HTTPException(status_code=400, detail="El período contable no existe para la fecha indicada.")
    
    if periodo.cerrado:
        raise HTTPException(status_code=400, detail="Operación rechazada: El período contable está cerrado.")

    codigos_cuentas = [mov.cuenta_codigo for mov in comprobante_in.movimientos]
    cuentas_db = db.query(PlanCuentas).filter(
        PlanCuentas.codigo.in_(codigos_cuentas),
        PlanCuentas.empresa_id == comprobante_in.empresa_id
    ).all()
    
    if len(cuentas_db) != len(set(codigos_cuentas)):
        raise HTTPException(status_code=400, detail="Una o más cuentas indicadas no existen.")
        
    for cuenta in cuentas_db:
        if not cuenta.activa:
            raise HTTPException(status_code=400, detail=f"La cuenta {cuenta.codigo} está inactiva.")

    cantidad_comprobantes = db.query(Comprobante).filter(
        Comprobante.periodo_id == periodo.id
    ).count()
    
    nuevo_consecutivo = f"COMP-{anio}{mes:02d}-{(cantidad_comprobantes + 1):05d}"

    nuevo_comprobante = Comprobante(
        empresa_id=comprobante_in.empresa_id,
        periodo_id=periodo.id,
        consecutivo=nuevo_consecutivo,
        fecha=comprobante_in.fecha,
        descripcion=comprobante_in.descripcion,
        estado="CONTABILIZADO"
    )
    db.add(nuevo_comprobante)
    db.flush()

    for mov in comprobante_in.movimientos:
        nuevo_mov = MovimientoContable(
            comprobante_id=nuevo_comprobante.id,
            cuenta_codigo=mov.cuenta_codigo,
            tercero_id=mov.tercero_id,
            debito=mov.debito,
            credito=mov.credito,
            descripcion=mov.descripcion
        )
        db.add(nuevo_mov)

    return nuevo_comprobante

def revertir_comprobante(db: Session, comprobante_id):
    comprobante = db.query(Comprobante).filter(Comprobante.id == comprobante_id).first()
    if not comprobante:
        raise HTTPException(status_code=404, detail="Comprobante no encontrado.")
    
    if comprobante.estado == "ANULADO":
        raise HTTPException(status_code=400, detail="No se puede revertir un comprobante anulado.")
    
    if comprobante.revertido:
        raise HTTPException(status_code=400, detail="El comprobante ya ha sido revertido.")

    periodo = db.query(PeriodoContable).filter(PeriodoContable.id == comprobante.periodo_id).with_for_update().first()
    if not periodo:
        raise HTTPException(status_code=400, detail="Período contable no encontrado.")

    if periodo.cerrado:
        raise HTTPException(status_code=400, detail="Operación rechazada: El período contable está cerrado.")

    if comprobante.estado != "CONTABILIZADO":
        raise HTTPException(status_code=400, detail="Solo se pueden revertir comprobantes en estado CONTABILIZADO.")

    cantidad_comprobantes = db.query(Comprobante).filter(
        Comprobante.periodo_id == periodo.id
    ).count()
    
    nuevo_consecutivo = f"COMP-{periodo.anio}{periodo.mes:02d}-{(cantidad_comprobantes + 1):05d}"

    nuevo_comprobante = Comprobante(
        empresa_id=comprobante.empresa_id,
        periodo_id=comprobante.periodo_id,
        consecutivo=nuevo_consecutivo,
        fecha=comprobante.fecha,
        descripcion=f"Reversión del comprobante {comprobante.consecutivo}",
        estado="CONTABILIZADO"
    )
    db.add(nuevo_comprobante)
    db.flush()

    for mov in comprobante.movimientos:
        nuevo_mov = MovimientoContable(
            comprobante_id=nuevo_comprobante.id,
            cuenta_codigo=mov.cuenta_codigo,
            tercero_id=mov.tercero_id,
            debito=mov.credito,
            credito=mov.debito,
            descripcion=mov.descripcion
        )
        db.add(nuevo_mov)

    db.flush()

    total_debito = sum(m.debito for m in nuevo_comprobante.movimientos)
    total_credito = sum(m.credito for m in nuevo_comprobante.movimientos)
    if total_debito != total_credito:
        raise HTTPException(status_code=400, detail="El comprobante de reversión está desbalanceado.")

    comprobante.revertido = True

    return nuevo_comprobante
