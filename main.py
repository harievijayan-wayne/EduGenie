"""
Root entrypoint for EduGenie FastAPI application.
Re-exports `app` from backend.main for Vercel and ASGI runners.
"""
from backend.main import app

__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
