import logging
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

# Sin esto, logger.info(...) en cualquier módulo (ver exogena_service.py,
# uvt_service.py) queda silenciado: Python solo muestra WARNING o superior
# cuando no se configura logging explícitamente, así que la trazabilidad
# de la regla 6.2.12 ("excluir con trazabilidad en el log") nunca llegaba
# a la consola aunque el código sí la ejecutara.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
from app.core.database import engine, Base
from app.core.database import Base
from app.core.security import obtener_usuario_actual
from app.core.seed import seed_admin_user, seed_datos_demo
from app.models.empresa import Empresa
from app.models.cuenta import PlanCuentas
from app.models.periodo import PeriodoContable
from app.models.comprobante import Comprobante, MovimientoContable
from app.models.tercero import Tercero
from app.models.uvt import UVTValue
from app.models.exogena import ExogenaGeneracion
from app.models.usuario import Usuario
from app.api.auth import router as auth_router
from app.api.comprobantes import router as comprobantes_router
from app.api.empresas import router as empresas_router
from app.api.reportes import router as reportes_router
from app.api.cuentas import router as cuentas_router
from app.api.periodos import router as periodos_router
from app.api.exogena import router as exogena_router
from app.api.terceros import router as terceros_router
# Importar el índice de modelos para que SQLAlchemy los reconozca
from app.models import base

# Crear las tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Usuario admin/admin123 para poder entrar al login recién levantado el
# proyecto (ver app/core/seed.py). Idempotente: no duplica en reinicios.
seed_admin_user()

# Empresa, plan de cuentas, terceros y un comprobante de ejemplo, para que
# "docker compose up" solo ya deje algo real con qué probar (incluida la
# exógena). También idempotente.
seed_datos_demo()

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

# Todo el API queda protegido con JWT excepto /api/auth (login) y el
# health check. Se aplica una sola vez aquí, a nivel de include_router, en
# vez de tocar cada router individual.
requiere_auth = [Depends(obtener_usuario_actual)]

app.include_router(auth_router, prefix="/api/auth", tags=["Autenticación"])
app.include_router(comprobantes_router, prefix="/api/comprobantes", tags=["Comprobantes"], dependencies=requiere_auth)
app.include_router(empresas_router, prefix="/api/empresas", tags=["Empresas"], dependencies=requiere_auth)
app.include_router(reportes_router, prefix="/api/reportes", tags=["Reportes"], dependencies=requiere_auth)
app.include_router(cuentas_router, prefix="/api/cuentas", tags=["Plan de Cuentas"], dependencies=requiere_auth)
app.include_router(periodos_router, prefix="/api/periodos", tags=["Periodos Contables"], dependencies=requiere_auth)
app.include_router(exogena_router, prefix="/api/exogena", tags=["Exógena"], dependencies=requiere_auth)
app.include_router(terceros_router, prefix="/api/terceros", tags=["Terceros"], dependencies=requiere_auth)

@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "ok", 
        "mensaje": "El motor contable está en línea y conectado."
    }