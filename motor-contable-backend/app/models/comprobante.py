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

    # Atribución de usuario para las operaciones relevantes del ciclo de
    # vida (regla 9.3: "deben ser auditables"). Nullable porque son
    # posteriores a la creación de la tabla y porque las pruebas que llaman
    # al service directamente no siempre autentican un usuario.
    creado_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    contabilizado_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    contabilizado_en = Column(DateTime(timezone=True), nullable=True)
    revertido_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    revertido_en = Column(DateTime(timezone=True), nullable=True)

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