"""
VetClaw - Vercel Serverless Adapter
Wraps the FastAPI app for Vercel Python runtime using Mangum (ASGI→WSGI)
"""
import os
import sys
import logging

logger = logging.getLogger("vetclaw.vercel")

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from main import app
    from mangum import Mangum
    handler = Mangum(app, lifespan="off")
    logger.info("VetClaw handler created successfully")
except Exception as e:
    logger.error(f"VetClaw app import failed: {e}", exc_info=True)
    # Fallback: create a minimal FastAPI app that reports the error
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    fallback_app = FastAPI(title="VetClaw (Error)")

    @fallback_app.get("/")
    @fallback_app.get("/{path:path}")
    async def error_handler(path: str = ""):
        return JSONResponse(
            status_code=503,
            content={
                "error": "App failed to initialize",
                "detail": str(e),
                "hint": "Check Vercel function logs for full traceback"
            }
        )

    handler = Mangum(fallback_app, lifespan="off")
