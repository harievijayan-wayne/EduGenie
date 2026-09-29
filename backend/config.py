import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "EduGenie"
    TAGLINE: str = "Learn Smarter. Understand Faster. Grow Better."
    VERSION: str = "1.0.0"
    
    # Environment & Security
    SECRET_KEY: str = "edugenie-super-secure-key-2026-production-ready"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database
    DATABASE_URL: str = "sqlite:///./edugenie.db"
    
    # AI Backend selector: "groq" | "ollama" | "demo"
    # groq   = Groq cloud inference (fastest, ~200 tok/s) ← recommended
    # ollama = Local Ollama server (offline, no API key needed)
    # demo   = Static fallback responses (no AI)
    AI_BACKEND: str = "groq"

    # Groq AI Configuration (used when AI_BACKEND=groq)
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "openai/gpt-oss-20b"   # GPT-compatible model on Groq

    # Ollama AI Configuration (used when AI_BACKEND=ollama)
    OLLAMA_MODEL: str = "qwen3:8b"
    OLLAMA_HOST: str = "http://localhost:11434"

    # Legacy — kept so old .env files don't break
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    DEMO_MODE: bool = False
    
    # Uploads & Storage
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 15
    ALLOWED_EXTENSIONS: list[str] = [".pdf", ".txt", ".docx", ".png", ".jpg", ".jpeg"]
    
    # Embeddings & RAG
    CHUNK_SIZE: int = 700
    CHUNK_OVERLAP: int = 120
    
    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs("backend/data", exist_ok=True)
