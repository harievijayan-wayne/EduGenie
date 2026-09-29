from typing import Dict, Any
from fastapi import APIRouter
from backend.services.gemini_service import gemini_service
from backend.config import settings

router = APIRouter(prefix="/api/health", tags=["Health"])

@router.get("")
def health_check() -> Dict[str, Any]:
    """Health check endpoint verifying application operational status."""
    return {
        "success": True,
        "status": "healthy",
        "service": "EduGenie",
        "version": settings.VERSION,
        "ai_backend": "ollama",
        "ai_configured": gemini_service.is_configured(),
        "demo_mode": not gemini_service.is_configured()
    }
