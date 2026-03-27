"""
VetClaw - Vercel Serverless Entry Point (Final)
Direct FastAPI ASGI export with fallback error handling.
Note: Vercel Python runtime has configuration issues.
Railway/Docker deployment recommended.
"""
import os
import sys

# Ensure project root is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from main import app
except Exception as e:
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    app = FastAPI(title="VetClaw (Error)")

    @app.get("/")
    @app.get("/{path:path}")
    async def error_handler(path: str = ""):
        return JSONResponse(
            status_code=503,
            content={"error": "Vercel config issue", "detail": str(e), "solution": "Use Railway/Docker"}
        )
