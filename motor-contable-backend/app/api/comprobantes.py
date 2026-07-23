from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.schemas.comprobante import ComprobanteCreate, ComprobanteResponse, ComprobanteReverseResponse
from app.services.comprobante_service import contabilizar_comprobante, revertir_comprobante
from app.models.comprobante import Comprobante
from uuid import UUID

router = APIRouter()

@router.get("/")
def listar_comprobantes(empresa_id: Optional[UUID] = None, consecutivo: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Comprobante)
    if empresa_id:
        query = query.filter(Comprobante.empresa_id == empresa_id)
    if consecutivo:
        query = query.filter(Comprobante.consecutivo.ilike(f"%{consecutivo}%"))
    comprobantes = query.all()
    return [
        {
            "id": c.id,
            "empresa_id": c.empresa_id,
            "periodo_id": c.periodo_id,
            "consecutivo": c.consecutivo,
            "fecha": c.fecha,
            "descripcion": c.descripcion,
            "estado": c.estado,
            "revertido": c.revertido,
            "created_at": c.created_at
        }
        for c in comprobantes
    ]

@router.get("/{comprobante_id}", response_model=ComprobanteResponse)
def obtener_comprobante(comprobante_id: UUID, db: Session = Depends(get_db)):
    comprobante = db.query(Comprobante).filter(Comprobante.id == comprobante_id).first()
    if not comprobante:
        raise HTTPException(status_code=404, detail="Comprobante no encontrado.")
    return comprobante

@router.post("/contabilizar")
def crear_comprobante(comprobante_in: ComprobanteCreate, db: Session = Depends(get_db)):
    try:
        comprobante = contabilizar_comprobante(db, comprobante_in)
        db.commit()
        db.refresh(comprobante)
        return {
            "mensaje": "Comprobante contabilizado con éxito",
            "consecutivo": comprobante.consecutivo,
            "id": comprobante.id
        }
    except HTTPException as http_exc:
        db.rollback()
        raise http_exc
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno del servidor al contabilizar.")

@router.post("/{comprobante_id}/revertir", response_model=ComprobanteReverseResponse)
def revertir_comprobante_endpoint(comprobante_id: UUID, db: Session = Depends(get_db)):
    try:
        nuevo_comprobante = revertir_comprobante(db, comprobante_id)
        db.commit()
        db.refresh(nuevo_comprobante)
        comprobante_original = db.query(Comprobante).filter(Comprobante.id == comprobante_id).first()
        return {
            "mensaje": "Comprobante revertido con éxito",
            "comprobante_original_id": comprobante_original.id,
            "comprobante_original_consecutivo": comprobante_original.consecutivo,
            "comprobante_nuevo_id": nuevo_comprobante.id,
            "comprobante_nuevo_consecutivo": nuevo_comprobante.consecutivo
        }
    except HTTPException as http_exc:
        db.rollback()
        raise http_exc
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno del servidor al revertir.")
