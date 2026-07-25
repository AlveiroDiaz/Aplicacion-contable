import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.empresa import Empresa
from app.schemas.empresa import EmpresaResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Empresas"])

@router.get("/", response_model=List[EmpresaResponse])
def obtener_empresas(db: Session = Depends(get_db)):
    try:
        # Consultamos solo las empresas activas
        empresas = db.query(Empresa).filter(Empresa.activa == True).all()
        return empresas
    except Exception:
        logger.exception("Error al consultar las empresas")
        raise HTTPException(status_code=500, detail="Error interno al consultar las empresas.")