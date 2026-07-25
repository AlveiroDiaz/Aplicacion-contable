from sqlalchemy.orm import Session
from fastapi import HTTPException
from pydantic import ValidationError
from app.models.comprobante import Comprobante, MovimientoContable
from app.models.periodo import PeriodoContable
from app.models.cuenta import PlanCuentas
from app.schemas.comprobante import ComprobanteCreate, MovimientoCreate, ComprobanteBorradorCreate
from decimal import Decimal


def _bloquear_periodo(db: Session, empresa_id, anio: int, mes: int, exigir_abierto: bool, lock: bool = True):
    query = db.query(PeriodoContable).filter(
        PeriodoContable.empresa_id == empresa_id,
        PeriodoContable.anio == anio,
        PeriodoContable.mes == mes
    )
    if lock:
        query = query.with_for_update()
    periodo = query.first()

    if not periodo:
        raise HTTPException(status_code=400, detail="El período contable no existe para la fecha indicada.")

    if exigir_abierto and periodo.cerrado:
        raise HTTPException(status_code=400, detail="Operación rechazada: El período contable está cerrado.")

    return periodo


def _validar_cuentas(db: Session, empresa_id, codigos_cuentas, exigir_activas: bool):
    if not codigos_cuentas:
        return

    cuentas_db = db.query(PlanCuentas).filter(
        PlanCuentas.codigo.in_(codigos_cuentas),
        PlanCuentas.empresa_id == empresa_id
    ).all()

    if len(cuentas_db) != len(set(codigos_cuentas)):
        raise HTTPException(status_code=400, detail="Una o más cuentas indicadas no existen.")

    if exigir_activas:
        for cuenta in cuentas_db:
            if not cuenta.activa:
                raise HTTPException(status_code=400, detail=f"La cuenta {cuenta.codigo} está inactiva.")


def _siguiente_consecutivo(db: Session, periodo: PeriodoContable) -> str:
    # Solo cuentan los comprobantes que ya recibieron folio (contabilizados o
    # reversiones); los borradores no consumen numeración.
    cantidad_comprobantes = db.query(Comprobante).filter(
        Comprobante.periodo_id == periodo.id,
        Comprobante.consecutivo.is_not(None)
    ).count()
    return f"COMP-{periodo.anio}{periodo.mes:02d}-{(cantidad_comprobantes + 1):05d}"


def _agregar_movimientos(db: Session, comprobante_id, movimientos):
    for mov in movimientos:
        db.add(MovimientoContable(
            comprobante_id=comprobante_id,
            cuenta_codigo=mov.cuenta_codigo,
            tercero_id=mov.tercero_id,
            debito=mov.debito,
            credito=mov.credito,
            descripcion=mov.descripcion
        ))


def contabilizar_comprobante(db: Session, comprobante_in: ComprobanteCreate):
    anio = comprobante_in.fecha.year
    mes = comprobante_in.fecha.month

    periodo = _bloquear_periodo(db, comprobante_in.empresa_id, anio, mes, exigir_abierto=True)
    _validar_cuentas(db, comprobante_in.empresa_id, [m.cuenta_codigo for m in comprobante_in.movimientos], exigir_activas=True)

    nuevo_comprobante = Comprobante(
        empresa_id=comprobante_in.empresa_id,
        periodo_id=periodo.id,
        consecutivo=_siguiente_consecutivo(db, periodo),
        fecha=comprobante_in.fecha,
        descripcion=comprobante_in.descripcion,
        estado="CONTABILIZADO"
    )
    db.add(nuevo_comprobante)
    db.flush()

    _agregar_movimientos(db, nuevo_comprobante.id, comprobante_in.movimientos)

    return nuevo_comprobante


def crear_borrador(db: Session, comprobante_in: ComprobanteBorradorCreate):
    """Guarda un comprobante en estado BORRADOR. A diferencia de
    contabilizar_comprobante, no exige partida doble, mínimo de líneas,
    cuentas activas ni período abierto: un borrador no afecta el libro
    mayor, así que puede quedar incompleto hasta que el usuario decida
    contabilizarlo (ver contabilizar_borrador)."""
    anio = comprobante_in.fecha.year
    mes = comprobante_in.fecha.month

    periodo = _bloquear_periodo(db, comprobante_in.empresa_id, anio, mes, exigir_abierto=False, lock=False)
    _validar_cuentas(db, comprobante_in.empresa_id, [m.cuenta_codigo for m in comprobante_in.movimientos], exigir_activas=False)

    nuevo_comprobante = Comprobante(
        empresa_id=comprobante_in.empresa_id,
        periodo_id=periodo.id,
        consecutivo=None,
        fecha=comprobante_in.fecha,
        descripcion=comprobante_in.descripcion,
        estado="BORRADOR"
    )
    db.add(nuevo_comprobante)
    db.flush()

    _agregar_movimientos(db, nuevo_comprobante.id, comprobante_in.movimientos)

    return nuevo_comprobante


def actualizar_borrador(db: Session, comprobante_id, comprobante_in: ComprobanteBorradorCreate):
    """Reemplaza por completo el encabezado y las líneas de un borrador
    existente. Solo es posible mientras el comprobante siga en BORRADOR:
    una vez contabilizado queda protegido (regla 3.3.7) y esta función lo
    rechaza."""
    comprobante = db.query(Comprobante).filter(Comprobante.id == comprobante_id).first()
    if not comprobante:
        raise HTTPException(status_code=404, detail="Comprobante no encontrado.")

    if comprobante.estado != "BORRADOR":
        raise HTTPException(status_code=400, detail="Solo se pueden editar comprobantes en estado BORRADOR.")

    anio = comprobante_in.fecha.year
    mes = comprobante_in.fecha.month

    periodo = _bloquear_periodo(db, comprobante_in.empresa_id, anio, mes, exigir_abierto=False, lock=False)
    _validar_cuentas(db, comprobante_in.empresa_id, [m.cuenta_codigo for m in comprobante_in.movimientos], exigir_activas=False)

    comprobante.empresa_id = comprobante_in.empresa_id
    comprobante.periodo_id = periodo.id
    comprobante.fecha = comprobante_in.fecha
    comprobante.descripcion = comprobante_in.descripcion

    db.query(MovimientoContable).filter(MovimientoContable.comprobante_id == comprobante.id).delete()
    db.flush()

    _agregar_movimientos(db, comprobante.id, comprobante_in.movimientos)
    db.flush()
    db.refresh(comprobante)

    return comprobante


def contabilizar_borrador(db: Session, comprobante_id):
    """Promueve un BORRADOR a CONTABILIZADO: aquí sí se exigen todas las
    reglas de la sección 3.3 (mínimo dos líneas, partida doble, cuentas
    activas, período abierto) y se asigna el consecutivo definitivo."""
    comprobante = db.query(Comprobante).filter(Comprobante.id == comprobante_id).with_for_update().first()
    if not comprobante:
        raise HTTPException(status_code=404, detail="Comprobante no encontrado.")

    if comprobante.estado != "BORRADOR":
        raise HTTPException(status_code=400, detail="Solo se pueden contabilizar comprobantes en estado BORRADOR.")

    movimientos_in = [
        MovimientoCreate(
            cuenta_codigo=mov.cuenta_codigo,
            tercero_id=mov.tercero_id,
            debito=mov.debito,
            credito=mov.credito,
            descripcion=mov.descripcion
        )
        for mov in comprobante.movimientos
    ]

    try:
        # Reutiliza las validaciones de ComprobanteCreate (mínimo dos líneas,
        # partida doble) sin duplicar esa lógica.
        ComprobanteCreate(
            empresa_id=comprobante.empresa_id,
            fecha=comprobante.fecha,
            descripcion=comprobante.descripcion,
            movimientos=movimientos_in
        )
    except ValidationError as exc:
        mensajes = "; ".join(error["msg"] for error in exc.errors())
        raise HTTPException(status_code=400, detail=mensajes)

    periodo = _bloquear_periodo(db, comprobante.empresa_id, comprobante.fecha.year, comprobante.fecha.month, exigir_abierto=True)
    _validar_cuentas(db, comprobante.empresa_id, [m.cuenta_codigo for m in movimientos_in], exigir_activas=True)

    comprobante.periodo_id = periodo.id
    comprobante.consecutivo = _siguiente_consecutivo(db, periodo)
    comprobante.estado = "CONTABILIZADO"
    db.flush()

    return comprobante


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

    nuevo_comprobante = Comprobante(
        empresa_id=comprobante.empresa_id,
        periodo_id=comprobante.periodo_id,
        consecutivo=_siguiente_consecutivo(db, periodo),
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
