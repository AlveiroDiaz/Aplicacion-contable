from app.core.database import SessionLocal
from app.models.empresa import Empresa

with SessionLocal() as db:
    empresas = db.query(Empresa).all()
    print('empresa count:', len(empresas))
    for e in empresas:
        print(e.id, e.nit, e.dv, e.razon_social, e.activa)
