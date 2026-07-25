from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.core.database import Base
from app.models.empresa import Empresa
from app.models.cuenta import PlanCuentas
from app.models.periodo import PeriodoContable
from app.models.comprobante import Comprobante, MovimientoContable
from app.models.tercero import Tercero
from app.models.uvt import UVTValue
from app.models.exogena import ExogenaGeneracion
from app.api.comprobantes import router as comprobantes_router 
from app.api.empresas import router as empresas_router
from app.api.reportes import router as reportes_router
from app.api.cuentas import router as cuentas_router
from app.api.periodos import router as periodos_router
from app.api.exogena import router as exogena_router
# Importar el índice de modelos para que SQLAlchemy los reconozca
from app.models import base 

# Crear las tablas en la base de datos
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)


app.add_middleware(
    CORSMiddleware,
    # Aquí autorizamos los puertos típicos de Next.js
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"], 
    allow_credentials=True,
    allow_methods=["*"], # Permite POST, GET, PUT, DELETE, etc.
    allow_headers=["*"], # Permite todos los headers
)

app.include_router(comprobantes_router, prefix="/api/comprobantes", tags=["Comprobantes"])
app.include_router(empresas_router, prefix="/api/empresas", tags=["Empresas"])
app.include_router(reportes_router, prefix="/api/reportes", tags=["Reportes"])
app.include_router(cuentas_router, prefix="/api/cuentas", tags=["Plan de Cuentas"])
app.include_router(periodos_router, prefix="/api/periodos", tags=["Periodos Contables"])
app.include_router(exogena_router, prefix="/api/exogena", tags=["Exógena"])

@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "ok", 
        "mensaje": "El motor contable está en línea y conectado."
    }