from datetime import date
from decimal import Decimal

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.usuario import Usuario
from app.models.empresa import Empresa
from app.models.periodo import PeriodoContable
from app.models.cuenta import PlanCuentas
from app.models.tercero import Tercero
from app.schemas.comprobante import ComprobanteCreate, MovimientoCreate
from app.services.comprobante_service import contabilizar_comprobante
from app.services.exogena_service import calcular_dv_nit

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"

DEMO_NIT = "800197268"
DEMO_RAZON_SOCIAL = "Empresa Demo SAS"


def seed_admin_user():
    """Crea un usuario admin/admin123 si todavía no existe ninguno con ese
    username. Idempotente: se puede llamar en cada arranque sin duplicar
    filas. Solo pensado para poder entrar al login recién levantado el
    proyecto (docker-compose incluido); cámbiala en cuanto tengas acceso."""
    db = SessionLocal()
    try:
        existe = db.query(Usuario).filter(Usuario.username == DEFAULT_ADMIN_USERNAME).first()
        if not existe:
            db.add(Usuario(
                username=DEFAULT_ADMIN_USERNAME,
                password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
                nombre="Administrador",
                activo=True,
            ))
            db.commit()
    finally:
        db.close()


def seed_datos_demo():
    """Deja una empresa, un plan de cuentas básico, un período abierto,
    un par de terceros y un comprobante contabilizado de ejemplo, para que
    'docker compose up' solo ya sirva para probar la app sin tener que
    crear nada a mano primero (incluida la exógena, que sin terceros con
    movimientos no tiene qué mostrar).

    Idempotente: si ya existe la empresa demo (por NIT), no hace nada."""
    db = SessionLocal()
    try:
        if db.query(Empresa).filter(Empresa.nit == DEMO_NIT).first():
            return

        empresa = Empresa(
            nit=DEMO_NIT,
            dv=calcular_dv_nit(DEMO_NIT),
            razon_social=DEMO_RAZON_SOCIAL,
            activa=True,
        )
        db.add(empresa)
        db.flush()

        hoy = date.today()
        periodo = PeriodoContable(
            empresa_id=empresa.id,
            anio=hoy.year,
            mes=hoy.month,
            cerrado=False,
        )
        db.add(periodo)

        # Prefijo "DEMO-": plan_cuentas.codigo es una llave única GLOBAL, no
        # por empresa (limitación conocida, ver README). Usar códigos
        # contables "normales" (5135, 2205, ...) aquí correría el riesgo de
        # chocar con cuentas que el usuario cree luego para otra empresa.
        cuentas = [
            PlanCuentas(codigo="DEMO-1105", empresa_id=empresa.id, nombre="Caja", naturaleza="DEBITO", activa=True),
            PlanCuentas(codigo="DEMO-5135", empresa_id=empresa.id, nombre="Honorarios", naturaleza="DEBITO", activa=True),
            PlanCuentas(codigo="DEMO-2408", empresa_id=empresa.id, nombre="IVA descontable", naturaleza="DEBITO", activa=True),
            PlanCuentas(codigo="DEMO-2205", empresa_id=empresa.id, nombre="Proveedores nacionales", naturaleza="CREDITO", activa=True),
            PlanCuentas(codigo="DEMO-4135", empresa_id=empresa.id, nombre="Ingresos por servicios", naturaleza="CREDITO", activa=True),
        ]
        db.add_all(cuentas)

        proveedor = Tercero(tipo_doc="NIT", num_doc="900555444", dv=calcular_dv_nit("900555444"), nombre="Proveedor Demo SAS")
        cliente = Tercero(tipo_doc="CC", num_doc="1020304050", nombre="Cliente Demo")
        db.add_all([proveedor, cliente])
        db.flush()

        # Comprobante de ejemplo, ya contabilizado, con un tercero por
        # encima del umbral típico (42 UVT) para que la exógena tenga algo
        # que mostrar apenas se genera, sin tener que crear nada a mano.
        contabilizar_comprobante(db, ComprobanteCreate(
            empresa_id=empresa.id,
            fecha=hoy,
            descripcion="Honorarios de consultoría (dato de demostración)",
            movimientos=[
                MovimientoCreate(cuenta_codigo="DEMO-5135", tercero_id=proveedor.id, debito=Decimal("5000000.00"), credito=Decimal("0.00")),
                MovimientoCreate(cuenta_codigo="DEMO-2408", debito=Decimal("950000.00"), credito=Decimal("0.00")),
                MovimientoCreate(cuenta_codigo="DEMO-2205", tercero_id=proveedor.id, debito=Decimal("0.00"), credito=Decimal("5950000.00")),
            ],
        ))

        db.commit()
    finally:
        db.close()
