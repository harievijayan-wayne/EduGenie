"""
Vercel Serverless Function entrypoint.
Exports the FastAPI app from backend.main.
"""
from backend.main import app

__all__ = ["app"]
