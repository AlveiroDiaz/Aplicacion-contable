from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.comprobante import ComprobanteCreate
from app.services.comprobante_service import contabilizar_comprobante

router = APIRouter()

@router.post("/contabilizar")
def crear_comprobante(comprobante_in: ComprobanteCreate, db: Session = Depends(get_db)):
    try:
        # Ejecutamos la lógica de negocio
        comprobante = contabilizar_comprobante(db, comprobante_in)
        
        # Si todo salió bien, confirmamos la transacción en la base de datos
        db.commit()
        db.refresh(comprobante)
        
        return {
            "mensaje": "Comprobante contabilizado con éxito",
            "consecutivo": comprobante.consecutivo,
            "id": comprobante.id
        }
    except HTTPException as http_exc:
        # Si nuestra lógica lanzó un error (ej. periodo cerrado), hacemos rollback y propagamos
        db.rollback()
        raise http_exc
    except Exception as e:
        # Si ocurre un error inesperado (ej. caída de red, error de sintaxis), garantizamos el rollback
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno del servidor al contabilizar.")