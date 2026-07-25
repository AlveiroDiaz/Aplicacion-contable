from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.tercero import Tercero
from app.schemas.tercero import TerceroCreate

def crear_tercero(db: Session, tercero_in: TerceroCreate):
    existente = db.query(Tercero).filter(Tercero.num_doc == tercero_in.num_doc).first()
    if existente:
        raise HTTPException(status_code=400, detail="Ya existe un tercero con ese número de documento.")

    nuevo_tercero = Tercero(**tercero_in.model_dump())
    db.add(nuevo_tercero)
    db.flush()
    db.refresh(nuevo_tercero)
    return nuevo_tercero

def buscar_terceros(db: Session, q: str = None):
    query = db.query(Tercero)
    if q:
        like = f"%{q}%"
        query = query.filter((Tercero.num_doc.ilike(like)) | (Tercero.nombre.ilike(like)))
    return query.order_by(Tercero.nombre).limit(50).all()
