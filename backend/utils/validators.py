import os
from fastapi import HTTPException, UploadFile, status
from backend.config import settings

def validate_uploaded_file(file: UploadFile) -> None:
    """Validates file extension and filename safety."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have a valid filename."
        )
    
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        allowed = ", ".join(settings.ALLOWED_EXTENSIONS)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension '{ext}' is not supported. Allowed formats: {allowed}"
        )

def sanitize_input_text(text: str, max_chars: int = 20000) -> str:
    """Sanitizes text and checks bounds to prevent payload abuse."""
    if not text or not text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Input text cannot be empty."
        )
    trimmed = text.strip()
    if len(trimmed) > max_chars:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Input exceeds maximum allowed limit of {max_chars} characters."
        )
    return trimmed
