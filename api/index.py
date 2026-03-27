"""
VetClaw - Vercel Serverless Entry Point (v3)
Direct FastAPI ASGI export - no Mangum wrapper.
Vercel's @vercel/python supports native ASGI since 2024.
"""
import os
import sys
import logging

logger = logging.getLogger("vetclaw.vercel")

# Ensure project root is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

logger.info(f"VetClaw v3 init: project_root={project_root}")

try:
    from main import app
    logger.info("VetClaw FastAPI app imported successfully")
except Exception as e:
    logger.error(f"VetClaw app import failed: {e}", exc_info=True)
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    app = FastAPI(title="VetClaw (Fallback)")

    @app.get("/")
    @app.get("/{path:path}")
    async def error_handler(path: str = ""):
        return JSONResponse(
            status_code=503,
            content={"error": "Main app import failed", "detail": str(e)}
        )
