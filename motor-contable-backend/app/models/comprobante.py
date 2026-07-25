import uuid
from sqlalchemy import Column, String, Date, Numeric, ForeignKey, DateTime, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class Comprobante(Base):
    __tablename__ = "comprobantes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)
    periodo_id = Column(UUID(as_uuid=True), ForeignKey("periodos_contables.id"), nullable=False)
    consecutivo = Column(String, nullable=True) # Se asigna al contabilizar
    fecha = Column(Date, nullable=False)
    descripcion = Column(String, nullable=False)
    estado = Column(String, default="BORRADOR") # BORRADOR, CONTABILIZADO, ANULADO
    revertido = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    periodo = relationship("PeriodoContable", back_populates="comprobantes")
    movimientos = relationship("MovimientoContable", back_populates="comprobante")

class MovimientoContable(Base):
    __tablename__ = "movimientos_contables"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    comprobante_id = Column(UUID(as_uuid=True), ForeignKey("comprobantes.id"), nullable=False)
    cuenta_codigo = Column(String, ForeignKey("plan_cuentas.codigo"), nullable=False)
    tercero_id = Column(UUID(as_uuid=True), ForeignKey("terceros.id"), nullable=True)
    
    # Uso ESTRICTO de Numeric para precisión monetaria (Escenario 5)
    debito = Column(Numeric(20, 2), default=0.00)
    credito = Column(Numeric(20, 2), default=0.00)
    descripcion = Column(String, nullable=True)

    comprobante = relationship("Comprobante", back_populates="movimientos")
    tercero = relationship("Tercero", back_populates="movimientos")