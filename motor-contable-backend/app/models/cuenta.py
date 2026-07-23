from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class PlanCuentas(Base):
    __tablename__ = "plan_cuentas"

    # En contabilidad, el código de la cuenta es el identificador natural ideal
    codigo = Column(String, primary_key=True, index=True)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)
    nombre = Column(String, nullable=False)
    naturaleza = Column(String, nullable=False) # 'DEBITO' o 'CREDITO'
    activa = Column(Boolean, default=True)
    parent_codigo = Column(String, ForeignKey("plan_cuentas.codigo"), nullable=True)