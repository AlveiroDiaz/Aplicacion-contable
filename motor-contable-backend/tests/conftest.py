"""
Infraestructura de pruebas.

Decisión de diseño: las pruebas corren contra una base de datos PostgreSQL real
(no SQLite en memoria), porque los modelos usan tipos específicos de Postgres
(UUID, Numeric) y varias reglas de negocio dependen de comportamiento real del
motor (bloqueo de filas con SELECT ... FOR UPDATE para el consecutivo). Probar
contra un motor distinto al de producción habría dado falsa confianza.

Cada test corre dentro de una transacción (con SAVEPOINTs) que se revierte al
finalizar, así que la base de datos de pruebas queda limpia entre tests sin
necesidad de recrear el esquema cada vez.
"""
import os

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql://postgres:1205@localhost:5432/motor_contable_test",
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

import pytest  # noqa: E402
from sqlalchemy import create_engine, event, text  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402


def _ensure_database_exists(url: str) -> None:
    db_name = make_url(url).database
    admin_url = make_url(url).set(database="postgres")
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    try:
        with admin_engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": db_name},
            ).scalar()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    finally:
        admin_engine.dispose()


_ensure_database_exists(TEST_DATABASE_URL)

# Importar la app DESPUÉS de fijar DATABASE_URL: main.py crea el engine y las
# tablas (Base.metadata.create_all) leyendo settings.DATABASE_URL en el import.
from app.core.database import engine, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.empresa import Empresa  # noqa: E402
from app.models.cuenta import PlanCuentas  # noqa: E402
from app.models.periodo import PeriodoContable  # noqa: E402
from app.services.exogena_service import calcular_dv_nit  # noqa: E402


@pytest.fixture()
def db():
    """Sesión ligada a una transacción externa que siempre se revierte.

    Usa el patrón de SAVEPOINT anidado de SQLAlchemy: si el código bajo
    prueba llama a session.commit() (como hacen los routers), en realidad
    libera el SAVEPOINT interno y se abre uno nuevo automáticamente, sin
    tocar la transacción externa. Al final del test, esa transacción externa
    se revierte y todo lo escrito desaparece.
    """
    connection = engine.connect()
    outer_transaction = connection.begin()
    session = Session(bind=connection)
    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(sess, transaction):
        if transaction.nested and not transaction._parent.nested:
            sess.begin_nested()

    try:
        yield session
    finally:
        session.close()
        if outer_transaction.is_active:
            outer_transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db):
    """TestClient que reutiliza la sesión de `db`, para que lo que el test
    prepara con `db` y lo que ocurre a través del API queden en la misma
    transacción (y se revierta todo junto al final)."""
    from fastapi.testclient import TestClient

    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
def empresa(db):
    nit = "900123456"
    empresa = Empresa(nit=nit, dv=calcular_dv_nit(nit), razon_social="Empresa Test SAS", activa=True)
    db.add(empresa)
    db.flush()
    return empresa


@pytest.fixture()
def periodo_abierto(db, empresa):
    periodo = PeriodoContable(empresa_id=empresa.id, anio=2025, mes=1, cerrado=False)
    db.add(periodo)
    db.flush()
    return periodo


@pytest.fixture()
def plan_cuentas(db, empresa):
    cuentas = {
        "5135": PlanCuentas(codigo="5135", empresa_id=empresa.id, nombre="Gasto operacional", naturaleza="DEBITO", activa=True),
        "2408": PlanCuentas(codigo="2408", empresa_id=empresa.id, nombre="IVA descontable", naturaleza="DEBITO", activa=True),
        "2205": PlanCuentas(codigo="2205", empresa_id=empresa.id, nombre="Proveedores", naturaleza="CREDITO", activa=True),
        "1105": PlanCuentas(codigo="1105", empresa_id=empresa.id, nombre="Caja", naturaleza="DEBITO", activa=True),
        "4135": PlanCuentas(codigo="4135", empresa_id=empresa.id, nombre="Ingresos", naturaleza="CREDITO", activa=True),
        "5199": PlanCuentas(codigo="5199", empresa_id=empresa.id, nombre="Cuenta inactiva", naturaleza="DEBITO", activa=False),
    }
    for cuenta in cuentas.values():
        db.add(cuenta)
    db.flush()
    return cuentas
