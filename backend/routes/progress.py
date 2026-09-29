import json
from typing import Dict, Any
from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, Progress, StudySession, Badge
from backend.schemas import ApiResponse
from backend.dependencies import get_current_user

router = APIRouter(prefix="/api/progress", tags=["Progress & Tracking"])

@router.get("", response_model=ApiResponse[Dict[str, Any]])
def get_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves learner progress, study time, streak, and badges."""
    prog = db.query(Progress).filter(Progress.user_id == current_user.id).first()
    if not prog:
        prog = Progress(user_id=current_user.id)
        db.add(prog)
        db.commit()
        db.refresh(prog)

    badges = db.query(Badge).filter(Badge.user_id == current_user.id).all()
    sessions = db.query(StudySession).filter(StudySession.user_id == current_user.id).order_by(StudySession.created_at.desc()).limit(10).all()

    return ApiResponse(
        success=True,
        message="Progress data retrieved.",
        data={
            "user": {
                "name": current_user.name,
                "email": current_user.email,
                "xp": current_user.xp,
                "streak": current_user.streak,
                "level": current_user.level
            },
            "stats": {
                "total_study_minutes": prog.total_study_minutes,
                "questions_asked": prog.questions_asked,
                "quizzes_completed": prog.quizzes_completed,
                "flashcards_reviewed": prog.flashcards_reviewed,
                "summaries_generated": prog.summaries_generated,
                "weak_topics": json.loads(prog.weak_topics_json or "[]"),
                "strong_topics": json.loads(prog.strong_topics_json or "[]")
            },
            "badges": [
                {"name": b.badge_name, "description": b.badge_description, "icon": b.icon, "earned_at": b.earned_at.isoformat()}
                for b in badges
            ],
            "recent_sessions": [
                {"topic": s.topic, "duration": s.duration_minutes, "type": s.session_type, "date": s.created_at.strftime("%Y-%m-%d %H:%M")}
                for s in sessions
            ]
        }
    )

@router.post("/session", response_model=ApiResponse[Dict[str, Any]])
def log_study_session(
    topic: str = Body(..., embed=True),
    duration_minutes: int = Body(25, embed=True),
    session_type: str = Body("practice", embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Logs a completed study or practice session."""
    session_record = StudySession(
        user_id=current_user.id,
        topic=topic,
        duration_minutes=duration_minutes,
        session_type=session_type
    )
    db.add(session_record)

    prog = db.query(Progress).filter(Progress.user_id == current_user.id).first()
    if prog:
        prog.total_study_minutes += duration_minutes

    current_user.xp = (current_user.xp or 0) + (duration_minutes * 2)
    db.commit()

    return ApiResponse(
        success=True,
        message=f"Logged {duration_minutes}m study session on '{topic}'. Earned {duration_minutes * 2} XP!",
        data={"total_minutes": prog.total_study_minutes if prog else duration_minutes}
    )
