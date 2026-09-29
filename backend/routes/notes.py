import json
from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, Note
from backend.schemas import NotesGenerateRequest, NotesResponse, ApiResponse
from backend.services.notes_service import notes_service
from backend.dependencies import get_current_user

router = APIRouter(prefix="/api/notes", tags=["Notes"])

@router.post("/generate", response_model=ApiResponse[NotesResponse])
def generate_notes(
    request: NotesGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generates comprehensive academic notes: definitions, key concepts, examples, exam points, quick revision."""
    notes_res = notes_service.generate_notes(request, db=db, user=current_user)
    current_user.xp = (current_user.xp or 0) + 15
    db.commit()

    return ApiResponse(
        success=True,
        message=f"Notes generated for '{request.topic}'.",
        data=notes_res
    )

@router.get("", response_model=ApiResponse[List[Dict[str, Any]]])
def list_notes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists saved notes for current student."""
    notes = db.query(Note).filter(Note.user_id == current_user.id).order_by(Note.created_at.desc()).limit(20).all()
    results = [
        {
            "id": n.id,
            "title": n.title,
            "note_type": n.note_type,
            "created_at": n.created_at.isoformat() if n.created_at else "",
            "content": json.loads(n.content_json)
        }
        for n in notes
    ]
    return ApiResponse(success=True, message="Saved notes retrieved.", data=results)
