"""
VetClaw - Vercel Serverless Entry Point
FastAPI ASGI app wrapped with Mangum for Vercel Python runtime compatibility.
"""
import os
import sys
import logging

logger = logging.getLogger("vetclaw.vercel")

# Ensure project root is in path (handle Vercel serverless path)
try:
    # Get the directory containing this file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    logger.info(f"Path setup: {project_root}")
except Exception as e:
    logger.error(f"Path setup failed: {e}")
    project_root = os.getcwd()
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

try:
    from main import app
    from mangum import Mangum
    handler = Mangum(app, lifespan="off")
    # Also export as 'app' for compatibility
    app = handler
    logger.info("VetClaw handler created successfully")
except Exception as e:
    logger.error(f"VetClaw app import failed: {e}", exc_info=True)
    # Create minimal fallback app
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

    from mangum import Mangum
    handler = Mangum(fallback_app, lifespan="off")
    app = handler
