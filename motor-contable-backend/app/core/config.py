from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Motor Contable API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # URL de conexión a PostgreSQL
    DATABASE_URL: str = "postgresql://postgres:1205@localhost:5432/motor_contable"
    UVT_SOURCE_URL: str = ""
    UVT_REFRESH_INTERVAL_DAYS: int = 30

    # Autenticación JWT. JWT_SECRET_KEY debe sobreescribirse vía variable de
    # entorno en cualquier entorno real (ver docker-compose.yml); el valor
    # por defecto solo sirve para desarrollo local.
    JWT_SECRET_KEY: str = "clave-de-desarrollo-cambiar-en-produccion"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480

    # Orígenes permitidos por CORS, separados por coma. Por defecto solo
    # localhost (desarrollo); en un servidor real hay que sobreescribirlo
    # con la URL pública real del frontend (ver docker-compose.yml / README).
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origen.strip() for origen in self.CORS_ORIGINS.split(",") if origen.strip()]

    class Config:
        case_sensitive = True

settings = Settings()