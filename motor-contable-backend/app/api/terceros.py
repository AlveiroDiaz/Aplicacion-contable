from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.schemas.tercero import TerceroCreate, TerceroResponse
from app.services.tercero_service import crear_tercero, buscar_terceros

router = APIRouter(tags=["Terceros"])

@router.get("/", response_model=List[TerceroResponse])
def listar_terceros(q: Optional[str] = None, db: Session = Depends(get_db)):
    try:
        return buscar_terceros(db, q)
    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno al listar terceros.")

@router.post("/", response_model=TerceroResponse)
def crear_tercero_endpoint(tercero_in: TerceroCreate, db: Session = Depends(get_db)):
    try:
        tercero = crear_tercero(db, tercero_in)
        db.commit()
        return tercero
    except HTTPException as http_exc:
        db.rollback()
        raise http_exc
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno al crear el tercero.")
