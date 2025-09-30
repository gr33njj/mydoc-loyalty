from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://mydoc_user:changeme123@postgres:5432/mydoc_loyalty"
    
    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    
    # Security
    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # 1C Integration
    ONEC_API_URL: Optional[str] = None
    ONEC_USERNAME: Optional[str] = None
    ONEC_PASSWORD: Optional[str] = None
    
    # Bitrix Integration
    BITRIX_API_URL: Optional[str] = None
    BITRIX_WEBHOOK: Optional[str] = None
    
    # Email (SMTP)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: str = "noreply@it-mydoc.ru"
    
    # SMS Gateway
    SMS_API_KEY: Optional[str] = None
    SMS_API_URL: str = "https://sms.ru/sms/send"
    
    # Application
    DOMAIN: str = "it-mydoc.ru"
    DEBUG: bool = False
    
    # File uploads
    UPLOAD_DIR: str = "/app/uploads"
    QR_CODE_DIR: str = "/app/qrcodes"
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB
    
    class Config:
        env_file = ".env"


settings = Settings()
