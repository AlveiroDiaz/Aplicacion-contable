from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.models.cuenta import PlanCuentas
from app.schemas.cuenta import PlanCuentaCreate, PlanCuentaUpdate, PlanCuentaResponse
from app.services.cuenta_service import (
    crear_cuenta,
    obtener_cuentas_por_empresa,
    obtener_cuenta_por_codigo,
    actualizar_cuenta,
    desactivar_cuenta,
)

router = APIRouter(tags=["Plan de Cuentas"])

@router.post("/", response_model=PlanCuentaResponse)
def crear_cuenta_endpoint(cuenta_in: PlanCuentaCreate, db: Session = Depends(get_db)):
    try:
        cuenta = crear_cuenta(db, cuenta_in)
        db.commit()
        return cuenta
    except HTTPException as http_exc:
        db.rollback()
        raise http_exc
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno al crear la cuenta.")

@router.get("/", response_model=List[PlanCuentaResponse])
def listar_cuentas(empresa_id: UUID, db: Session = Depends(get_db)):
    try:
        cuentas = obtener_cuentas_por_empresa(db, empresa_id)
        return cuentas
    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno al listar cuentas.")

@router.get("/{codigo}", response_model=PlanCuentaResponse)
def obtener_cuenta_endpoint(codigo: str, empresa_id: UUID, db: Session = Depends(get_db)):
    try:
        cuenta = obtener_cuenta_por_codigo(db, codigo, empresa_id)
        return cuenta
    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno al consultar la cuenta.")

@router.put("/{codigo}", response_model=PlanCuentaResponse)
def actualizar_cuenta_endpoint(codigo: str, empresa_id: UUID, cuenta_in: PlanCuentaUpdate, db: Session = Depends(get_db)):
    try:
        cuenta = actualizar_cuenta(db, codigo, empresa_id, cuenta_in)
        db.commit()
        return cuenta
    except HTTPException as http_exc:
        db.rollback()
        raise http_exc
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno al actualizar la cuenta.")

@router.delete("/{codigo}")
def desactivar_cuenta_endpoint(codigo: str, empresa_id: UUID, db: Session = Depends(get_db)):
    try:
        desactivar_cuenta(db, codigo, empresa_id)
        db.commit()
        return {"mensaje": "Cuenta desactivada correctamente."}
    except HTTPException as http_exc:
        db.rollback()
        raise http_exc
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno al desactivar la cuenta.")
