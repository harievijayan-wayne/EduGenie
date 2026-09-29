from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User
from backend.schemas import ExplainRequest, ExplainResponse, ApiResponse
from backend.services.explanation_service import explanation_service
from backend.dependencies import get_current_user

router = APIRouter(prefix="/api/explain", tags=["Explanation"])

@router.post("", response_model=ApiResponse[ExplainResponse])
def explain_concept(
    request: ExplainRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Concept Explanation:
    Supports: Simple English, ELI5, Tamil, Tanglish.
    Returns: concept, simple_explanation, example, real_world_example, key_points, common_mistakes.
    """
    res = explanation_service.explain_concept(request)

    # Award XP for curiosity
    current_user.xp = (current_user.xp or 0) + 10
    db.commit()

    return ApiResponse(
        success=True,
        message=f"Explanation for '{request.topic}' generated.",
        data=res
    )
