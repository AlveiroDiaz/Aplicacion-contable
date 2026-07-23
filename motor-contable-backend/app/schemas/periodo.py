from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class PeriodoResponse(BaseModel):
    id: UUID
    empresa_id: UUID
    anio: int
    mes: int
    cerrado: bool

    class Config:
        from_attributes = True

class PeriodoCerrarRequest(BaseModel):
    empresa_id: UUID
    anio: int
    mes: int
