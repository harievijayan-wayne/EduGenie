from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, Progress
from backend.schemas import SummaryRequest, SummaryResponse, ApiResponse
from backend.services.summary_service import summary_service
from backend.dependencies import get_current_user

router = APIRouter(prefix="/api/summarize", tags=["Summary"])

@router.post("", response_model=ApiResponse[SummaryResponse])
def summarize_content(
    request: SummaryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Summarizes text into Short, Medium, or Detailed formats with key points and definitions."""
    summary_res = summary_service.summarize(request)

    # Award XP and increment count
    current_user.xp = (current_user.xp or 0) + 15
    progress = db.query(Progress).filter(Progress.user_id == current_user.id).first()
    if progress:
        progress.summaries_generated = (progress.summaries_generated or 0) + 1
    db.commit()

    return ApiResponse(
        success=True,
        message=f"{request.summary_length} summary generated successfully.",
        data=summary_res
    )
