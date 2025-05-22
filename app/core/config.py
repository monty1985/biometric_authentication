from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Voice Authentication API"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Voice Authentication Settings
    MIN_VOICE_SAMPLE_DURATION: float = 3.0  # seconds
    MAX_VOICE_SAMPLE_DURATION: float = 10.0  # seconds
    SIMILARITY_THRESHOLD: float = 0.85  # Minimum similarity score for verification
    
    # Vector Store Settings
    VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", "data/embeddings")
    
    # Anti-spoofing Settings
    SPOOF_THRESHOLD: float = 0.5  # Maximum score to consider as genuine
    
    # Storage Settings
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "data/uploads")
    
    class Config:
        case_sensitive = True

settings = Settings() 