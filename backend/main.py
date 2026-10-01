import os
import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.database import engine, Base, SessionLocal
from backend.models import User, Progress, Badge
from backend.routes import all_routers
from backend.utils.security import hash_password

logger = logging.getLogger("edugenie.main")
logging.basicConfig(level=logging.INFO)

def seed_initial_data():
    """Seeds rich initial data if database is fresh."""
    db = SessionLocal()
    try:
        user_count = db.query(User).count()
        if user_count == 0:
            logger.info("Initializing fresh database with demo scholar...")
            demo_user = User(
                name="Alex Scholar",
                email="demo@edugenie.ai",
                hashed_password=hash_password("edugenie123"),
                xp=350,
                streak=5,
                level="Active Scholar"
            )
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)

            progress = Progress(
                user_id=demo_user.id,
                total_study_minutes=240,
                questions_asked=12,
                quizzes_completed=5,
                flashcards_reviewed=24,
                summaries_generated=4,
                weak_topics_json='["SQL JOINs", "Binary Search Trees", "Dynamic Programming"]',
                strong_topics_json='["Array Traversal", "REST APIs", "Python Basics"]'
            )
            db.add(progress)

            badges = [
                Badge(user_id=demo_user.id, badge_name="First Quiz", badge_description="Completed your first diagnostic quiz!", icon="trophy"),
                Badge(user_id=demo_user.id, badge_name="Consistent Scholar", badge_description="Maintained a 5-day active streak!", icon="flame"),
                Badge(user_id=demo_user.id, badge_name="Topic Explorer", badge_description="Studied multiple computer science topics!", icon="compass"),
                Badge(user_id=demo_user.id, badge_name="Revision Hero", badge_description="Reviewed 20+ active recall flashcards!", icon="book-open")
            ]
            for b in badges:
                db.add(b)

            db.commit()
            logger.info("Seed data successfully populated!")
    except Exception as e:
        logger.warning(f"Seed data error: {e}")
    finally:
        db.close()

def init_db():
    """Initializes the database schema and seeds initial data safely."""
    try:
        Base.metadata.create_all(bind=engine)
        seed_initial_data()
        logger.info("EduGenie database successfully initialized.")
    except Exception as e:
        logger.warning(f"Database initialization deferred or skipped: {e}")

# Safe startup in lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
    logger.info("EduGenie shutting down gracefully.")

app = FastAPI(
    title=settings.APP_NAME,
    description="Google Gemini Powered AI Learning Assistant - Learn Smarter. Understand Faster. Grow Better.",
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "frontend", "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "frontend", "templates")

# Safely mount static directory if it exists
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=TEMPLATES_DIR if os.path.exists(TEMPLATES_DIR) else ".")

# Register all API routers
for router in all_routers:
    app.include_router(router)

# ----------------- Frontend HTML Routes -----------------

@app.get("/", response_class=HTMLResponse)
def index_page(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"settings": settings})

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={"settings": settings})

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(request=request, name="register.html", context={"settings": settings})

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html", context={"settings": settings, "active_page": "dashboard"})

@app.get("/chat", response_class=HTMLResponse)
def chat_page(request: Request):
    return templates.TemplateResponse(request=request, name="chat.html", context={"settings": settings, "active_page": "chat", "mode": "qa"})

@app.get("/tutor", response_class=HTMLResponse)
def tutor_page(request: Request):
    return templates.TemplateResponse(request=request, name="chat.html", context={"settings": settings, "active_page": "tutor", "mode": "tutor"})

@app.get("/quiz", response_class=HTMLResponse)
def quiz_page(request: Request):
    return templates.TemplateResponse(request=request, name="quiz.html", context={"settings": settings, "active_page": "quiz"})

@app.get("/documents", response_class=HTMLResponse)
def documents_page(request: Request):
    return templates.TemplateResponse(request=request, name="documents.html", context={"settings": settings, "active_page": "documents"})

@app.get("/learning-path", response_class=HTMLResponse)
def learning_path_page(request: Request):
    return templates.TemplateResponse(request=request, name="learning_path.html", context={"settings": settings, "active_page": "learning_path"})

@app.get("/flashcards", response_class=HTMLResponse)
def flashcards_page(request: Request):
    return templates.TemplateResponse(request=request, name="flashcards.html", context={"settings": settings, "active_page": "flashcards"})

@app.get("/notes", response_class=HTMLResponse)
def notes_page(request: Request):
    return templates.TemplateResponse(request=request, name="notes.html", context={"settings": settings, "active_page": "notes"})

@app.get("/exam", response_class=HTMLResponse)
def exam_page(request: Request):
    return templates.TemplateResponse(request=request, name="exam.html", context={"settings": settings, "active_page": "exam"})

@app.get("/progress", response_class=HTMLResponse)
def progress_page(request: Request):
    return templates.TemplateResponse(request=request, name="progress.html", context={"settings": settings, "active_page": "progress"})
