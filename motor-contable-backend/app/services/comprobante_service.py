from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.comprobante import Comprobante, MovimientoContable
from app.models.periodo import PeriodoContable
from app.models.cuenta import PlanCuentas
from app.schemas.comprobante import ComprobanteCreate

def contabilizar_comprobante(db: Session, comprobante_in: ComprobanteCreate):
    # 1. Extraer año y mes para buscar el período
    anio = comprobante_in.fecha.year
    mes = comprobante_in.fecha.month

    # 2. Bloqueo transaccional y validación de Período (Escenarios 4 y 6)
    # .with_for_update() hace un ROW LOCK en PostgreSQL. 
    # Evita que dos peticiones concurrentes lean el mismo estado del periodo a la vez.
    periodo = db.query(PeriodoContable).filter(
        PeriodoContable.empresa_id == comprobante_in.empresa_id,
        PeriodoContable.anio == anio,
        PeriodoContable.mes == mes
    ).with_for_update().first() 

    if not periodo:
        raise HTTPException(status_code=400, detail="El período contable no existe para la fecha indicada.")
    
    # Regla: Que el período contable esté abierto
    if periodo.cerrado:
        raise HTTPException(status_code=400, detail="Operación rechazada: El período contable está cerrado.")

    # 3. Validar que las cuentas existan y estén activas
    codigos_cuentas = [mov.cuenta_codigo for mov in comprobante_in.movimientos]
    cuentas_db = db.query(PlanCuentas).filter(
        PlanCuentas.codigo.in_(codigos_cuentas),
        PlanCuentas.empresa_id == comprobante_in.empresa_id
    ).all()
    
    if len(cuentas_db) != len(set(codigos_cuentas)):
        raise HTTPException(status_code=400, detail="Una o más cuentas indicadas no existen.")
        
    for cuenta in cuentas_db:
        # Regla: Que todas las cuentas utilizadas estén activas
        if not cuenta.activa:
            raise HTTPException(status_code=400, detail=f"La cuenta {cuenta.codigo} está inactiva.")

    # 4. Generar Consecutivo
    # Gracias a with_for_update() arriba, este conteo es seguro en concurrencia
    cantidad_comprobantes = db.query(Comprobante).filter(
        Comprobante.periodo_id == periodo.id
    ).count()
    
    nuevo_consecutivo = f"COMP-{anio}{mes:02d}-{(cantidad_comprobantes + 1):05d}"

    # 5. Crear la cabecera del Comprobante
    nuevo_comprobante = Comprobante(
        empresa_id=comprobante_in.empresa_id,
        periodo_id=periodo.id,
        consecutivo=nuevo_consecutivo,
        fecha=comprobante_in.fecha,
        descripcion=comprobante_in.descripcion,
        estado="CONTABILIZADO"
    )
    db.add(nuevo_comprobante)
    db.flush() # Envía el INSERT a la DB para obtener el ID, pero NO hace commit aún.

    # 6. Crear los movimientos contables
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

    # Retornamos el objeto. El Commit de la transacción se hará en la capa de API (Router).
    return nuevo_comprobante