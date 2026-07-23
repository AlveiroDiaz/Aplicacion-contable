from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

# 1. Importamos la base de datos usando tu ruta correcta
from app.core.database import get_db

# 2. Importamos el modelo y el esquema (Asegúrate de que los nombres de archivo coincidan con los tuyos)
# Asumiendo que creaste un archivo empresa.py dentro de app/models/ y app/schemas/
from app.models.empresa import Empresa 
from app.schemas.empresa import EmpresaResponse

# 3. Si en tu main.py ya declaras el prefijo "/api/empresas", aquí solo necesitas el router
router = APIRouter(tags=["Empresas"])

@router.get("/", response_model=List[EmpresaResponse])
def obtener_empresas(db: Session = Depends(get_db)):
    try:
        # Consultamos solo las empresas activas
        empresas = db.query(Empresa).filter(Empresa.activa == True).all()
        return empresas
    except Exception as e:
        # Mantenemos tu buena práctica de capturar excepciones y evitar que el servidor colapse
        raise HTTPException(status_code=500, detail="Error interno al consultar las empresas.")