from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Agents Stock API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
