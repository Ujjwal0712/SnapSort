"""
Application Settings
Load configuration from environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "SnapSort API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = ""
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database - PostgreSQL
    DATABASE_URL: str 
    
    # Redis
    REDIS_URL: str 
    
    # Qdrant Vector Database
    QDRANT_HOST: str 
    QDRANT_PORT: int 
    QDRANT_COLLECTION: str = "face_embeddings"
    
    # AWS S3
    AWS_ACCESS_KEY_ID: Optional[str] 
    AWS_SECRET_ACCESS_KEY: Optional[str] 
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = "snapsort-photos"
    
    # Cloudinary (for image transformations)
    CLOUDINARY_CLOUD_NAME: Optional[str]
    CLOUDINARY_API_KEY: Optional[str]
    CLOUDINARY_API_SECRET: Optional[str] 
    
    # JWT Authentication
    JWT_SECRET_KEY: str 
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Face Recognition
    FACE_MATCH_THRESHOLD: float = 0.85
    PRIMARY_FACE_PROVIDER: str = "deepface"  # deepface, insightface, aws, google
    
    # AWS Rekognition (optional)
    AWS_REKOGNITION_REGION: str = "us-east-1"
    
    # Google Cloud Vision (optional)
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] 
    
    # Celery
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str 

    # Connection pool configuration
    POOL_MIN_SIZE: int = 5
    POOL_MAX_SIZE: int = 20

    MAILERSEND_API_KEY: str
    MAILERSEND_FROM_EMAIL: str = "22160@iiitu.ac.in"

    OTP_LENGTH: int = 6
    OTP_EXPIRY_MINUTES: int = 10
    MAX_ATTEMPTS: int = 3
    
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()
