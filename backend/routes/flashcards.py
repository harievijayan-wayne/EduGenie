from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, Flashcard, Progress
from backend.schemas import FlashcardGenerateRequest, FlashcardResponse, FlashcardItem, ApiResponse
from backend.services.flashcard_service import flashcard_service
from backend.dependencies import get_current_user

router = APIRouter(prefix="/api/flashcards", tags=["Flashcards"])

@router.post("/generate", response_model=ApiResponse[FlashcardResponse])
def generate_flashcards(
    request: FlashcardGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generates active recall flashcards with question, answer, hint, and difficulty."""
    cards_res = flashcard_service.generate_flashcards(request, db=db, user=current_user)
    
    current_user.xp = (current_user.xp or 0) + 15
    progress = db.query(Progress).filter(Progress.user_id == current_user.id).first()
    if progress:
        progress.flashcards_reviewed = (progress.flashcards_reviewed or 0) + len(cards_res.flashcards)
    db.commit()

    return ApiResponse(
        success=True,
        message=f"Generated {len(cards_res.flashcards)} flashcards for '{request.topic}'.",
        data=cards_res
    )

@router.get("", response_model=ApiResponse[List[FlashcardItem]])
def list_flashcards(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists saved flashcards for active recall study."""
    cards = db.query(Flashcard).filter(Flashcard.user_id == current_user.id).order_by(Flashcard.created_at.desc()).limit(50).all()
    items = [
        FlashcardItem(
            id=c.id,
            question=c.question,
            answer=c.answer,
            hint=c.hint,
            difficulty=c.difficulty,
            is_known=c.is_known,
            is_difficult=c.is_difficult
        )
        for c in cards
    ]
    return ApiResponse(success=True, message="Flashcards loaded.", data=items)

@router.put("/{card_id}/status", response_model=ApiResponse[FlashcardItem])
def update_card_status(
    card_id: int,
    is_known: bool = False,
    is_difficult: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Updates mastery status (known vs difficult) for spaced repetition."""
    card = db.query(Flashcard).filter(Flashcard.id == card_id, Flashcard.user_id == current_user.id).first()
    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flashcard not found.")

    card.is_known = is_known
    card.is_difficult = is_difficult
    db.commit()
    db.refresh(card)

    return ApiResponse(
        success=True,
        message="Card status updated.",
        data=FlashcardItem(
            id=card.id,
            question=card.question,
            answer=card.answer,
            hint=card.hint,
            difficulty=card.difficulty,
            is_known=card.is_known,
            is_difficult=card.is_difficult
        )
    )
