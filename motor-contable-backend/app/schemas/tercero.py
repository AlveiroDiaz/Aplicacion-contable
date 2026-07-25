from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class TerceroCreate(BaseModel):
    tipo_doc: Optional[str] = None
    num_doc: str
    dv: Optional[str] = None
    nombre: str

class TerceroResponse(BaseModel):
    id: UUID
    tipo_doc: Optional[str] = None
    num_doc: Optional[str] = None
    dv: Optional[str] = None
    nombre: Optional[str] = None

    class Config:
        from_attributes = True
