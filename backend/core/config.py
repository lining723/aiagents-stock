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

    REDIS_ENABLED: bool = True
    REDIS_URL: str = "redis://127.0.0.1:6379/0"
    REDIS_KEY_PREFIX: str = "aiagents-stock"

    # 不同数据类型的缓存时长。TTL 是新鲜缓存时间，STALE_TTL 是源数据失败时可兜底使用的最长时间。
    CACHE_TTL_REALTIME_SECONDS: int = 30
    CACHE_TTL_TECHNICAL_SECONDS: int = 1800
    CACHE_TTL_KLINE_SECONDS: int = 1800
    CACHE_TTL_FUNDAMENTAL_SECONDS: int = 43200
    CACHE_TTL_FUND_FLOW_SECONDS: int = 1800
    CACHE_TTL_NEWS_SECONDS: int = 1800
    CACHE_TTL_LONGHUBANG_SECONDS: int = 86400
    CACHE_TTL_PRICE_PREDICTION_SECONDS: int = 300

    CACHE_STALE_TTL_REALTIME_SECONDS: int = 300
    CACHE_STALE_TTL_TECHNICAL_SECONDS: int = 86400
    CACHE_STALE_TTL_KLINE_SECONDS: int = 86400
    CACHE_STALE_TTL_FUNDAMENTAL_SECONDS: int = 604800
    CACHE_STALE_TTL_FUND_FLOW_SECONDS: int = 86400
    CACHE_STALE_TTL_NEWS_SECONDS: int = 86400
    CACHE_STALE_TTL_LONGHUBANG_SECONDS: int = 604800
    CACHE_STALE_TTL_PRICE_PREDICTION_SECONDS: int = 1800
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
