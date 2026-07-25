import uuid
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class Tercero(Base):
    __tablename__ = "terceros"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tipo_doc = Column(String, nullable=True)
    num_doc = Column(String, nullable=True, index=True)
    dv = Column(String, nullable=True)
    nombre = Column(String, nullable=True)

    movimientos = relationship("MovimientoContable", back_populates="tercero")
