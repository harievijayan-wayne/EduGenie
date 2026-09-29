import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, TutorConversation
from backend.schemas import TutorChatRequest, TutorChatResponse, ApiResponse
from backend.services.tutor_service import tutor_service
from backend.dependencies import get_current_user

router = APIRouter(prefix="/api/tutor", tags=["AI Tutor"])

@router.post("/chat", response_model=ApiResponse[TutorChatResponse])
def chat_with_tutor(
    request: TutorChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Engages in Socratic pedagogical dialogue with EduGenie AI Tutor.
    Responds to queries and special actions like 'Explain Simpler', 'Give Example', 'Quiz Me', and 'I Don't Understand'.
    """
    tutor_reply = tutor_service.chat_with_tutor(request, db=db, user=current_user)
    current_user.xp = (current_user.xp or 0) + 10
    db.commit()

    return ApiResponse(
        success=True,
        message="Tutor response generated.",
        data=tutor_reply
    )

@router.get("/history/{conversation_id}", response_model=ApiResponse[list])
def get_conversation_history(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Loads chat history for a session."""
    conv = db.query(TutorConversation).filter(TutorConversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    history = json.loads(conv.history_json or "[]")
    return ApiResponse(
        success=True,
        message="Conversation history loaded.",
        data=history
    )
