import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, Quiz
from backend.schemas import (
    QuizGenerateRequest, QuizResponse, QuizQuestion,
    QuizSubmitRequest, QuizEvaluationResponse, ApiResponse
)
from backend.services.quiz_service import quiz_service
from backend.dependencies import get_current_user

router = APIRouter(prefix="/api/quiz", tags=["Quiz"])

@router.post("/generate", response_model=ApiResponse[QuizResponse])
def generate_quiz(
    request: QuizGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generates 3, 5, or 10 MCQ quiz questions on chosen academic topic with difficulty."""
    quiz_res = quiz_service.generate_quiz(request, db=db, user_id=current_user.id)
    return ApiResponse(
        success=True,
        message=f"Generated {quiz_res.total_questions} quiz questions for '{request.topic}'.",
        data=quiz_res
    )

@router.post("/submit", response_model=ApiResponse[QuizEvaluationResponse])
def submit_quiz(
    submission: QuizSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Evaluates submitted answers, computes accuracy, records attempt, identifies weak areas."""
    evaluation = quiz_service.evaluate_quiz(submission, db=db, user=current_user)
    return ApiResponse(
        success=True,
        message=f"Quiz evaluated! You scored {evaluation.score}/{evaluation.total_questions} ({evaluation.percentage}%).",
        data=evaluation
    )

@router.get("/{quiz_id}", response_model=ApiResponse[QuizResponse])
def get_quiz(
    quiz_id: int,
    db: Session = Depends(get_db)
):
    """Fetches a saved quiz by ID for re-attempts."""
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found.")

    raw_questions = json.loads(quiz.questions_json)
    questions = [QuizQuestion(**q) for q in raw_questions]

    return ApiResponse(
        success=True,
        message="Quiz loaded.",
        data=QuizResponse(
            quiz_id=quiz.id,
            topic=quiz.topic,
            difficulty=quiz.difficulty,
            total_questions=quiz.total_questions,
            questions=questions
        )
    )
