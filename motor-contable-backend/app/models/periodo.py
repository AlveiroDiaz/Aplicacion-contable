import uuid
from sqlalchemy import Column, Integer, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class PeriodoContable(Base):
    __tablename__ = "periodos_contables"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)
    anio = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=False)
    cerrado = Column(Boolean, default=False)

    comprobantes = relationship("Comprobante", back_populates="periodo", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('empresa_id', 'anio', 'mes', name='uq_empresa_periodo'),
    )