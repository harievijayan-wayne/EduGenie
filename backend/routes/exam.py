from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User
from backend.schemas import ExamAnswerRequest, ExamAnswerResponse, ApiResponse
from backend.services.exam_service import exam_service
from backend.dependencies import get_current_user

router = APIRouter(prefix="/api/exam", tags=["Exam Answer Generator"])

@router.post("/generate", response_model=ApiResponse[ExamAnswerResponse])
def generate_exam_answer(
    request: ExamAnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generates university-standard answers tailored for:
    2 Marks, 5 Marks, 10 Marks, 13 Marks, or 16 Marks.
    Includes time tips, word count estimates, diagrams, and complete structure.
    """
    ans_res = exam_service.generate_exam_answer(request)
    current_user.xp = (current_user.xp or 0) + 20
    db.commit()

    return ApiResponse(
        success=True,
        message=f"Exam answer generated for {request.marks} marks on '{request.topic}'.",
        data=ans_res
    )
