from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from backend.database import get_db, SessionLocal
from backend.models import User, Progress
from backend.utils.security import decode_access_token

security_scheme = HTTPBearer(auto_error=False)

def get_or_create_demo_user(db: Session) -> User:
    """Provides a default demo user for seamless out-of-the-box exploration."""
    demo = db.query(User).filter(User.email == "demo@edugenie.ai").first()
    if not demo:
        from backend.utils.security import hash_password
        demo = User(
            name="Alex Scholar",
            email="demo@edugenie.ai",
            hashed_password=hash_password("edugenie123"),
            xp=320,
            streak=5,
            level="Active Learner"
        )
        db.add(demo)
        db.commit()
        db.refresh(demo)

        # Setup initial progress record
        progress = Progress(
            user_id=demo.id,
            total_study_minutes=240,
            questions_asked=12,
            quizzes_completed=4,
            flashcards_reviewed=18,
            summaries_generated=3,
            weak_topics_json='["SQL JOINs", "Binary Search Trees", "Dynamic Programming"]',
            strong_topics_json='["Array Traversal", "REST APIs", "Python Basics"]'
        )
        db.add(progress)
        db.commit()

    return demo

def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Extracts current authenticated user from Authorization Bearer token
    or from cookie 'access_token'. Falls back to demo user if not logged in.
    """
    token = None
    if credentials:
        token = credentials.credentials
    elif "access_token" in request.cookies:
        token = request.cookies.get("access_token")

    if token:
        payload = decode_access_token(token)
        if payload and "sub" in payload:
            user_email = payload["sub"]
            user = db.query(User).filter(User.email == user_email).first()
            if user:
                return user

    # If no token or invalid, return default demo user so all endpoints work
    return get_or_create_demo_user(db)

def get_required_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Strict authentication requirement."""
    token = None
    if credentials:
        token = credentials.credentials
    elif "access_token" in request.cookies:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is required."
        )

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token."
        )

    user = db.query(User).filter(User.email == payload["sub"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
    return user
