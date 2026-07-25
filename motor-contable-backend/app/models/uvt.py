import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, Numeric, String, DateTime, Text, func
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class UVTValue(Base):
    __tablename__ = "uvt_values"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    anio = Column(Integer, unique=True, nullable=False, index=True)
    valor = Column(Numeric(20, 2), nullable=False)
    fuente = Column(String, nullable=False)
    status = Column(String, nullable=False, default="SUCCESS")
    error = Column(Text, nullable=True)
    fetched_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
