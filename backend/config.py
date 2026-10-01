import os
from typing import Optional
from pydantic_settings import BaseSettings

def _detect_serverless() -> bool:
    """Detect if running in a serverless, container, or read-only cloud environment."""
    if any(os.environ.get(k) for k in ("VERCEL", "VERCEL_ENV", "NOW_REGION", "AWS_LAMBDA_FUNCTION_NAME", "LAMBDA_TASK_ROOT")):
        return True
    if os.path.exists("/var/task"):
        return True
    # Test if current working directory is writable
    try:
        test_file = os.path.join(os.getcwd(), ".write_test_tmp")
        with open(test_file, "w") as f:
            f.write("1")
        os.remove(test_file)
        return False
    except (OSError, IOError, PermissionError):
        return True

IS_VERCEL = _detect_serverless()

_DEFAULT_DB_URL = "sqlite:////tmp/edugenie.db" if IS_VERCEL else "sqlite:///./edugenie.db"
_DEFAULT_UPLOAD_DIR = "/tmp/uploads" if IS_VERCEL else "uploads"

class Settings(BaseSettings):
    APP_NAME: str = "EduGenie"
    TAGLINE: str = "Learn Smarter. Understand Faster. Grow Better."
    VERSION: str = "1.0.0"
    
    # Environment & Security
    SECRET_KEY: str = "edugenie-super-secure-key-2026-production-ready"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database
    DATABASE_URL: str = _DEFAULT_DB_URL
    
    # AI Backend selector: "groq" | "ollama" | "demo"
    # groq   = Groq cloud inference (fastest, ~200 tok/s) ← recommended for Vercel
    # ollama = Local Ollama server (offline, local machine only)
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
    UPLOAD_DIR: str = _DEFAULT_UPLOAD_DIR
    MAX_UPLOAD_SIZE_MB: int = 15
    ALLOWED_EXTENSIONS: list[str] = [".pdf", ".txt", ".docx", ".png", ".jpg", ".jpeg"]
    
    # Embeddings & RAG
    CHUNK_SIZE: int = 700
    CHUNK_OVERLAP: int = 120
    
    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()

# On Vercel / serverless: ensure SQLite databases point to writable /tmp
if IS_VERCEL and "sqlite" in settings.DATABASE_URL:
    if not settings.DATABASE_URL.startswith("sqlite:////tmp/"):
        db_filename = os.path.basename(settings.DATABASE_URL.replace("sqlite:///", "")) or "edugenie.db"
        settings.DATABASE_URL = f"sqlite:////tmp/{db_filename}"

# If running on Vercel with SQLite in /tmp, copy initial seed database if available
if IS_VERCEL and "sqlite" in settings.DATABASE_URL and "/tmp/" in settings.DATABASE_URL:
    try:
        import shutil
        seed_db = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "edugenie.db")
        target_db = settings.DATABASE_URL.replace("sqlite:///", "")
        if os.path.exists(seed_db) and not os.path.exists(target_db):
            shutil.copy2(seed_db, target_db)
    except Exception:
        pass

# Ensure directories exist safely without throwing on read-only filesystems
try:
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    if not IS_VERCEL:
        os.makedirs("backend/data", exist_ok=True)
    else:
        os.makedirs("/tmp/data", exist_ok=True)
except OSError:
    pass

