from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import date, datetime
from uuid import UUID
from decimal import Decimal

class MovimientoCreate(BaseModel):
    cuenta_codigo: str
    tercero_id: Optional[UUID] = None
    debito: Decimal = Field(default=Decimal('0.00'), ge=0)
    credito: Decimal = Field(default=Decimal('0.00'), ge=0)
    descripcion: Optional[str] = None

    @field_validator('credito')
    def validate_movimiento(cls, credito, info):
        debito = info.data.get('debito', Decimal('0.00'))
        if debito > 0 and credito > 0:
            raise ValueError('Una línea no puede tener valores en débito y crédito simultáneamente')
        if debito == 0 and credito == 0:
            raise ValueError('La línea debe tener un valor en débito o en crédito')
        return credito

class ComprobanteCreate(BaseModel):
    empresa_id: UUID
    fecha: date
    descripcion: str
    movimientos: List[MovimientoCreate]

    @field_validator('movimientos')
    def validate_partida_doble(cls, movimientos):
        if len(movimientos) < 2:
            raise ValueError('El comprobante debe tener al menos dos líneas contables')
        total_debito = sum(m.debito for m in movimientos)
        total_credito = sum(m.credito for m in movimientos)
        if total_debito != total_credito:
            raise ValueError(f'El comprobante está desbalanceado. Débitos: {total_debito}, Créditos: {total_credito}')
        return movimientos

class MovimientoResponse(BaseModel):
    id: UUID
    cuenta_codigo: str
    debito: Decimal
    credito: Decimal
    descripcion: Optional[str] = None

    class Config:
        from_attributes = True

class ComprobanteResponse(BaseModel):
    id: UUID
    empresa_id: UUID
    periodo_id: UUID
    consecutivo: str
    fecha: date
    descripcion: str
    estado: str
    revertido: bool
    created_at: Optional[datetime] = None
    movimientos: List[MovimientoResponse]

    class Config:
        from_attributes = True

class ComprobanteReverseResponse(BaseModel):
    mensaje: str
    comprobante_original_id: UUID
    comprobante_original_consecutivo: str
    comprobante_nuevo_id: UUID
    comprobante_nuevo_consecutivo: str
