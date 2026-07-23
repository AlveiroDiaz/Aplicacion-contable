from pydantic import BaseModel, field_validator
from typing import Optional
from uuid import UUID

class PlanCuentaCreate(BaseModel):
    codigo: str
    empresa_id: UUID
    nombre: str
    naturaleza: str
    activa: bool = True
    parent_codigo: Optional[str] = None

    @field_validator('naturaleza')
    def validate_naturaleza(cls, v):
        if v not in ('DEBITO', 'CREDITO'):
            raise ValueError('La naturaleza debe ser DEBITO o CREDITO')
        return v

class PlanCuentaUpdate(BaseModel):
    nombre: Optional[str] = None
    naturaleza: Optional[str] = None
    activa: Optional[bool] = None
    parent_codigo: Optional[str] = None

    @field_validator('naturaleza')
    def validate_naturaleza(cls, v):
        if v is not None and v not in ('DEBITO', 'CREDITO'):
            raise ValueError('La naturaleza debe ser DEBITO o CREDITO')
        return v

class PlanCuentaResponse(BaseModel):
    codigo: str
    empresa_id: UUID
    nombre: str
    naturaleza: str
    activa: bool
    parent_codigo: Optional[str] = None

    class Config:
        from_attributes = True
