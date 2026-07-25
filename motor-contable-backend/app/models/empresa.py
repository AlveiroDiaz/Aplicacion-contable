import uuid
from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class Empresa(Base):
    __tablename__ = "empresas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nit = Column(String, unique=True, index=True, nullable=False)
    dv = Column(String, nullable=True)
    razon_social = Column(String, nullable=False)
    activa = Column(Boolean, default=True)