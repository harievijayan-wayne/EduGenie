from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, Progress, Badge
from backend.schemas import UserRegister, UserLogin, UserOut, TokenResponse, ApiResponse
from backend.utils.security import hash_password, verify_password, create_access_token
from backend.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=ApiResponse[TokenResponse])
def register(user_data: UserRegister, response: Response, db: Session = Depends(get_db)):
    """Registers a new student account, hashes password, and creates session."""
    existing = db.query(User).filter(User.email == user_data.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    hashed_pw = hash_password(user_data.password)
    new_user = User(
        name=user_data.name,
        email=user_data.email.lower(),
        hashed_password=hashed_pw,
        xp=100,
        streak=1,
        level="Novice Scholar"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Initialize learner progress
    init_progress = Progress(
        user_id=new_user.id,
        total_study_minutes=60,
        questions_asked=0,
        quizzes_completed=0,
        flashcards_reviewed=0,
        summaries_generated=0,
        weak_topics_json="[]",
        strong_topics_json="[]"
    )
    db.add(init_progress)

    # Welcome badge
    welcome_badge = Badge(
        user_id=new_user.id,
        badge_name="Welcome Scholar",
        badge_description="Joined the EduGenie AI learning universe!",
        icon="sparkles"
    )
    db.add(welcome_badge)
    db.commit()

    token = create_access_token({"sub": new_user.email})
    response.set_cookie(key="access_token", value=token, httponly=True, max_age=60*60*24*7)

    return ApiResponse(
        success=True,
        message="Registration successful! Welcome to EduGenie.",
        data=TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserOut.model_validate(new_user)
        )
    )

@router.post("/login", response_model=ApiResponse[TokenResponse])
def login(login_data: UserLogin, response: Response, db: Session = Depends(get_db)):
    """Authenticates student credentials and returns a secure token."""
    user = db.query(User).filter(User.email == login_data.email.lower()).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    token = create_access_token({"sub": user.email})
    response.set_cookie(key="access_token", value=token, httponly=True, max_age=60*60*24*7)

    return ApiResponse(
        success=True,
        message="Welcome back!",
        data=TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserOut.model_validate(user)
        )
    )

@router.post("/logout", response_model=ApiResponse[Dict[str, str]])
def logout(response: Response):
    """Clears access token cookie."""
    response.delete_cookie(key="access_token")
    return ApiResponse(
        success=True,
        message="Logged out successfully.",
        data={"status": "logged_out"}
    )

@router.get("/me", response_model=ApiResponse[UserOut])
def get_profile(current_user: User = Depends(get_current_user)):
    """Fetches currently logged-in student profile."""
    return ApiResponse(
        success=True,
        message="User profile retrieved.",
        data=UserOut.model_validate(current_user)
    )
