from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "JalRakshak AI"
    API_V1_STR: str = "/api/v1"
    
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "jalrakshak_db_pass"
    POSTGRES_DB: str = "jalrakshak"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:jalrakshak_db_pass@localhost:5432/jalrakshak"
    
    REDIS_URL: str = "redis://localhost:6379/0"
    
    SECRET_KEY: str = "supersecretkey-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Optional API Keys
    GEMINI_API_KEY: str | None = None

    class Config:
        env_file = ".env"

settings = Settings()
