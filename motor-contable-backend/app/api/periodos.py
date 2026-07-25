from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.models.periodo import PeriodoContable
from app.models.empresa import Empresa
from app.models.comprobante import Comprobante
from app.schemas.periodo import PeriodoResponse, PeriodoCerrarRequest

router = APIRouter(tags=["Periodos Contables"])

@router.get("/", response_model=List[PeriodoResponse])
def listar_periodos(
    empresa_id: Optional[UUID] = Query(None),
    cerrado: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(PeriodoContable)
    if empresa_id:
        query = query.filter(PeriodoContable.empresa_id == empresa_id)
    if cerrado is not None:
        query = query.filter(PeriodoContable.cerrado == cerrado)
    periodos = query.order_by(PeriodoContable.anio.desc(), PeriodoContable.mes.desc()).all()
    return periodos

@router.post("/cerrar", response_model=PeriodoResponse)
def cerrar_periodo(payload: PeriodoCerrarRequest, db: Session = Depends(get_db)):
    periodo = db.query(PeriodoContable).filter(
        PeriodoContable.empresa_id == payload.empresa_id,
        PeriodoContable.anio == payload.anio,
        PeriodoContable.mes == payload.mes
    ).first()

    if not periodo:
        raise HTTPException(status_code=404, detail="El período contable no existe.")

    if periodo.cerrado:
        raise HTTPException(status_code=400, detail="El período ya está cerrado.")

    comprobantes_pendientes = db.query(Comprobante).filter(
        Comprobante.periodo_id == periodo.id,
        Comprobante.estado == "BORRADOR"
    ).count()

    if comprobantes_pendientes > 0:
        raise HTTPException(status_code=400, detail="No se puede cerrar el período porque tiene comprobantes en borrador sin contabilizar.")

    periodo.cerrado = True
    db.commit()
    db.refresh(periodo)
    return periodo
