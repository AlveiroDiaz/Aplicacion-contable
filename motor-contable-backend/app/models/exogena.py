import uuid
from sqlalchemy import Column, String, DateTime, Integer, Numeric, ForeignKey, JSON, Text, func
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class ExogenaGeneracion(Base):
    __tablename__ = "exogena_generaciones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)
    anio_gravable = Column(Integer, nullable=False)
    fecha_generacion = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    parametros = Column(JSON, nullable=False)
    registros = Column(Integer, nullable=False, default=0)
    total_valor_bruto = Column(Numeric(20, 2), nullable=False, default=0)
    total_retencion = Column(Numeric(20, 2), nullable=False, default=0)
    archivo_xml = Column(Text, nullable=False)
