from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import date
from uuid import UUID
from decimal import Decimal

class MovimientoCreate(BaseModel):
    cuenta_codigo: str
    tercero_id: Optional[UUID] = None
    # Usamos Decimal para mantener la precisión monetaria exacta
    debito: Decimal = Field(default=Decimal('0.00'), ge=0)
    credito: Decimal = Field(default=Decimal('0.00'), ge=0)
    descripcion: Optional[str] = None

    @field_validator('credito')
    def validate_movimiento(cls, credito, info):
        debito = info.data.get('debito', Decimal('0.00'))
        
        # Regla: Que ninguna línea tenga simultáneamente débito y crédito
        if debito > 0 and credito > 0:
            raise ValueError('Una línea no puede tener valores en débito y crédito simultáneamente')
        
        # Regla: Que los valores sean válidos (positivos, y al menos uno debe ser mayor a 0)
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
        # Regla: Que tenga al menos dos líneas
        if len(movimientos) < 2:
            raise ValueError('El comprobante debe tener al menos dos líneas contables')
        
        total_debito = sum(m.debito for m in movimientos)
        total_credito = sum(m.credito for m in movimientos)
        
        # Regla: Que el total de débitos sea igual al total de créditos (partida doble)
        if total_debito != total_credito:
            raise ValueError(f'El comprobante está desbalanceado. Débitos: {total_debito}, Créditos: {total_credito}')
            
        return movimientos