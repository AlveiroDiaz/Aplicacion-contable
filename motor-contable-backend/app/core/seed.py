from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.usuario import Usuario

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"


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
