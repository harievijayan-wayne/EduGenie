from backend.routes.auth import router as auth_router
from backend.routes.qa import router as qa_router
from backend.routes.explain import router as explain_router
from backend.routes.quiz import router as quiz_router
from backend.routes.summary import router as summary_router
from backend.routes.learning import router as learning_router
from backend.routes.documents import router as documents_router
from backend.routes.flashcards import router as flashcards_router
from backend.routes.notes import router as notes_router
from backend.routes.exam import router as exam_router
from backend.routes.tutor import router as tutor_router
from backend.routes.progress import router as progress_router
from backend.routes.dashboard import router as dashboard_router
from backend.routes.health import router as health_router

all_routers = [
    auth_router,
    qa_router,
    explain_router,
    quiz_router,
    summary_router,
    learning_router,
    documents_router,
    flashcards_router,
    notes_router,
    exam_router,
    tutor_router,
    progress_router,
    dashboard_router,
    health_router,
]
