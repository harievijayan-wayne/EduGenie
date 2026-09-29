from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User
from backend.schemas import DashboardMetricsResponse, ApiResponse
from backend.services.analytics_service import analytics_service
from backend.dependencies import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/metrics", response_model=ApiResponse[DashboardMetricsResponse])
def get_dashboard_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetches high-level metrics, XP, streak, quiz accuracy, weekly activity, and badge statuses."""
    metrics = analytics_service.get_dashboard_metrics(current_user, db)
    return ApiResponse(
        success=True,
        message="Dashboard metrics retrieved.",
        data=metrics
    )

@router.get("/recommendations", response_model=ApiResponse[List[Dict[str, Any]]])
def get_adaptive_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Adaptive Learning recommendations derived from student's weak areas and quiz performance.
    Labelled transparently as AI-Generated Recommendations.
    """
    metrics = analytics_service.get_dashboard_metrics(current_user, db)
    recommendations = []
    for topic in metrics.weak_areas[:3]:
        recommendations.append({
            "topic": topic,
            "badge": "AI Diagnostic",
            "type": "Weak Area Mastery",
            "suggested_flow": [
                f"{topic} Concept Basics",
                f"{topic} Common Traps & Pitfalls",
                f"{topic} 5-Minute Practice Quiz"
            ]
        })

    return ApiResponse(
        success=True,
        message="Adaptive learning recommendations retrieved.",
        data=recommendations
    )
