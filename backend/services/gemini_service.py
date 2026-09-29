"""
EduGenie AI Service — routing layer

Points `gemini_service` at whichever backend is configured via AI_BACKEND:
  - "groq"   : Groq cloud (ultra-fast, ~200 tok/s)  ← default
  - "ollama" : Local Ollama (qwen3:8b)
  - "demo"   : Static fallbacks (no API key needed)

All routes/services import `gemini_service` and work unchanged.
"""
import logging
from backend.config import settings

logger = logging.getLogger("edugenie.ai")

_backend = (settings.AI_BACKEND or "groq").lower()

if _backend == "groq":
    from backend.services.groq_service import groq_service as gemini_service  # noqa: F401
elif _backend == "ollama":
    from backend.services.ollama_service import ollama_service as gemini_service  # noqa: F401
else:
    # Demo / fallback — use Ollama service which has rich static responses
    from backend.services.ollama_service import ollama_service as gemini_service  # noqa: F401

logger.info(f"AI backend active: {_backend.upper()}")

__all__ = ["gemini_service"]
