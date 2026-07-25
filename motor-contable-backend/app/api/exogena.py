from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import extract
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.empresa import Empresa
from app.models.comprobante import MovimientoContable, Comprobante
from app.models.exogena import ExogenaGeneracion
from app.services.uvt_service import get_uvt
from app.services.exogena_service import (
    agrupar_movimientos_por_tercero_concepto,
    build_exogena_xml,
    filtrar_registros_por_umbral,
    validar_nit_con_dv,
    construir_parametros,
)

router = APIRouter(tags=["Exógena"])


class ExogenaGenerateRequest(BaseModel):
    empresa_id: UUID
    anio_gravable: int
    umbral_uvt: int
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None


class ExogenaHistoryItem(BaseModel):
    id: UUID
    empresa_id: UUID
    anio_gravable: int
    fecha_generacion: datetime
    parametros: dict
    registros: int
    total_valor_bruto: Decimal
    total_retencion: Decimal

    class Config:
        from_attributes = True


@router.post("/generar", response_model=None)
def generar_exogena(
    payload: ExogenaGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    try:
        empresa = db.query(Empresa).filter(Empresa.id == payload.empresa_id).first()
        print("Empresa encontrada:", empresa.dv )
        if not empresa:
            raise HTTPException(status_code=404, detail="Empresa no encontrada")

        if not validar_nit_con_dv(empresa.nit, empresa.dv if hasattr(empresa, "dv") else "0"):
            raise HTTPException(status_code=400, detail="El NIT del informante no es válido")

        uvt_row = get_uvt(db, payload.anio_gravable, background_task=background_tasks)
        valor_uvt = Decimal(uvt_row.valor)
        umbral_pesos = valor_uvt * Decimal(payload.umbral_uvt)

        query = db.query(MovimientoContable, Comprobante).join(Comprobante, MovimientoContable.comprobante).filter(
            MovimientoContable.tercero_id.is_not(None),
            Comprobante.empresa_id == payload.empresa_id,
            extract("year", Comprobante.fecha) == payload.anio_gravable,
        )

        print("Query de movimientos construida:", query)

        if payload.fecha_inicio:
            query = query.filter(Comprobante.fecha >= payload.fecha_inicio)
        if payload.fecha_fin:
            query = query.filter(Comprobante.fecha <= payload.fecha_fin)

        movimientos = query.order_by(Comprobante.fecha, Comprobante.consecutivo).all()
        agrupados = agrupar_movimientos_por_tercero_concepto(movimientos)
        registros, excluidos = filtrar_registros_por_umbral(agrupados, umbral_pesos)

        total_valor_bruto = sum(r["valor_bruto"] for r in registros)
        total_retencion = sum(r["valor_retencion"] for r in registros)

        xml_content = build_exogena_xml(empresa, payload.anio_gravable, registros, total_valor_bruto, total_retencion)
        generacion = ExogenaGeneracion(
            empresa_id=payload.empresa_id,
            anio_gravable=payload.anio_gravable,
            parametros=construir_parametros(payload.anio_gravable, payload.umbral_uvt, valor_uvt, payload.fecha_inicio, payload.fecha_fin),
            registros=len(registros),
            total_valor_bruto=total_valor_bruto,
            total_retencion=total_retencion,
            archivo_xml=xml_content,
        )
        db.add(generacion)
        db.commit()
        db.refresh(generacion)

        filename = f"exogena-{payload.empresa_id}-{payload.anio_gravable}.xml"
        return StreamingResponse(
            iter([xml_content.encode("utf-8")]),
            media_type="application/xml",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error al generar exógena: {e}")
        raise HTTPException(status_code=500, detail="Error interno al generar el archivo de exógena.") from e


@router.get("/historial", response_model=List[ExogenaHistoryItem])
def historial_exogena(db: Session = Depends(get_db)):
    try:
        items = db.query(ExogenaGeneracion).order_by(ExogenaGeneracion.fecha_generacion.desc()).all()
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno al consultar el historial de exógena.") from e


@router.get("/historial/{id}/archivo")
def descargar_archivo(id: UUID, db: Session = Depends(get_db)):
    try:
        generacion = db.query(ExogenaGeneracion).filter(ExogenaGeneracion.id == id).first()
        if not generacion:
            raise HTTPException(status_code=404, detail="Generación no encontrada")

        filename = f"exogena-{generacion.empresa_id}-{generacion.anio_gravable}.xml"
        return StreamingResponse(
            iter([generacion.archivo_xml.encode("utf-8")]),
            media_type="application/xml",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno al descargar el archivo de exógena.") from e
