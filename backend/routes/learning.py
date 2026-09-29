import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, LearningPath
from backend.schemas import (
    LearningPathRequest, LearningPathResponse,
    StudyPlanRequest, StudyPlanResponse, ApiResponse
)
from backend.services.learning_path_service import learning_path_service
from backend.dependencies import get_current_user

router = APIRouter(prefix="/api", tags=["Learning Path & Study Plan"])

@router.post("/learn/recommendations", response_model=ApiResponse[LearningPathResponse])
def get_learning_path(
    request: LearningPathRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generates a 6-stage structured educational mastery roadmap:
    Beginner -> Fundamentals -> Intermediate -> Advanced -> Projects -> Assessment
    """
    path_res = learning_path_service.generate_learning_path(request)

    # Persist in database
    db_path = LearningPath(
        user_id=current_user.id,
        topic=request.topic,
        current_level=request.current_level,
        goal=request.goal,
        hours_per_day=request.hours_per_day,
        duration=request.duration,
        stages_json=json.dumps([s.model_dump() for s in path_res.stages])
    )
    db.add(db_path)
    current_user.xp = (current_user.xp or 0) + 25
    db.commit()

    return ApiResponse(
        success=True,
        message=f"Custom learning roadmap generated for {request.topic}.",
        data=path_res
    )

@router.post("/learning/study-plan", response_model=ApiResponse[StudyPlanResponse])
def get_study_plan(
    request: StudyPlanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generates an actionable daily calendar study schedule leading up to target exam date."""
    plan_res = learning_path_service.generate_study_plan(request)
    current_user.xp = (current_user.xp or 0) + 20
    db.commit()

    return ApiResponse(
        success=True,
        message="Daily study calendar schedule generated.",
        data=plan_res
    )
