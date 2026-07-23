from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.cuenta import PlanCuentas
from app.schemas.cuenta import PlanCuentaCreate, PlanCuentaUpdate

def crear_cuenta(db: Session, cuenta_in: PlanCuentaCreate):
    existente = db.query(PlanCuentas).filter(
        PlanCuentas.codigo == cuenta_in.codigo,
        PlanCuentas.empresa_id == cuenta_in.empresa_id
    ).first()
    if existente:
        raise HTTPException(status_code=400, detail="El código de cuenta ya existe para esta empresa.")

    if cuenta_in.parent_codigo:
        parent = db.query(PlanCuentas).filter(
            PlanCuentas.codigo == cuenta_in.parent_codigo,
            PlanCuentas.empresa_id == cuenta_in.empresa_id
        ).first()
        if not parent:
            raise HTTPException(status_code=400, detail="La cuenta padre no existe para esta empresa.")

    nueva_cuenta = PlanCuentas(**cuenta_in.model_dump())
    db.add(nueva_cuenta)
    db.flush()
    db.refresh(nueva_cuenta)
    return nueva_cuenta

def obtener_cuentas_por_empresa(db: Session, empresa_id):
    return db.query(PlanCuentas).filter(
        PlanCuentas.empresa_id == empresa_id,
        PlanCuentas.activa == True
    ).all()

def obtener_cuenta_por_codigo(db: Session, codigo: str, empresa_id):
    cuenta = db.query(PlanCuentas).filter(
        PlanCuentas.codigo == codigo,
        PlanCuentas.empresa_id == empresa_id
    ).first()
    if not cuenta:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada.")
    return cuenta

def actualizar_cuenta(db: Session, codigo: str, empresa_id, cuenta_in: PlanCuentaUpdate):
    cuenta = db.query(PlanCuentas).filter(
        PlanCuentas.codigo == codigo,
        PlanCuentas.empresa_id == empresa_id
    ).first()
    if not cuenta:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada.")

    datos = cuenta_in.model_dump(exclude_unset=True)

    if 'naturaleza' in datos and datos['naturaleza']:
        if datos['naturaleza'] not in ('DEBITO', 'CREDITO'):
            raise HTTPException(status_code=400, detail="La naturaleza debe ser DEBITO o CREDITO")

    if 'parent_codigo' in datos and datos['parent_codigo']:
        parent = db.query(PlanCuentas).filter(
            PlanCuentas.codigo == datos['parent_codigo'],
            PlanCuentas.empresa_id == empresa_id
        ).first()
        if not parent:
            raise HTTPException(status_code=400, detail="La cuenta padre no existe para esta empresa.")

    for key, value in datos.items():
        setattr(cuenta, key, value)

    db.flush()
    db.refresh(cuenta)
    return cuenta

def desactivar_cuenta(db: Session, codigo: str, empresa_id):
    cuenta = db.query(PlanCuentas).filter(
        PlanCuentas.codigo == codigo,
        PlanCuentas.empresa_id == empresa_id
    ).first()
    if not cuenta:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada.")

    cuenta.activa = False
    db.flush()
    db.refresh(cuenta)
    return cuenta
