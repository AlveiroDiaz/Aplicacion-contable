from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Motor Contable API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # URL de conexión a PostgreSQL
    DATABASE_URL: str = "postgresql://postgres:1205@localhost:5432/motor_contable"

    class Config:
        case_sensitive = True

settings = Settings()