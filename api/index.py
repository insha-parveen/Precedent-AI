"""Vercel Serverless Entrypoint for FastAPI backend.
"""
from src.precedent.api import app

# Vercel looks for the ASGI app instance named 'app'
__all__ = ["app"]
