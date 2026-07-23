from pydantic import BaseModel
from uuid import UUID

class EmpresaResponse(BaseModel):
    id: UUID
    nit: str
    razon_social: str
    activa: bool

    class Config:
        # Si usas Pydantic v2 (lo más común actualmente)
        from_attributes = True 
        
        # Si usas Pydantic v1 (versiones más antiguas de FastAPI), comenta la línea de arriba y usa esta:
        # orm_mode = True