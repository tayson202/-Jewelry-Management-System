from pydantic_settings import BaseSettings
from typing import List
from decimal import Decimal

class Settings(BaseSettings):
    PROJECT_NAME: str = "StockPilot - Gold & Jewelry Management System (AURUM OS)"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "AURUM_SECRET_KEY_CHANGE_IN_PRODUCTION_999_9"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database: Default SQLite for local standalone execution, easily overridden by POSTGRES_URL in .env
    DATABASE_URL: str = "sqlite:///./stockpilot.db"

    # Default Gold Market Constants (Sagha / Cairo Bullion Desk)
    DEFAULT_CURRENCY: str = "EGP"
    DEFAULT_24K_BASE_RATE: Decimal = Decimal("3420.00")
    DEFAULT_TAX_RATE_ON_MAKING: Decimal = Decimal("0.14")  # 14% Egyptian ETA VAT on workmanship only

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
