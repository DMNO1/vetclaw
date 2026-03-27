"""
VetClaw - Vercel Serverless Entry Point (v2)
Self-contained minimal test to isolate Vercel Python runtime issues.
"""
import os
import sys
import logging

logger = logging.getLogger("vetclaw.vercel")
logging.basicConfig(level=logging.INFO)

# Ensure project root is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

logger.info(f"VetClaw v2 init: project_root={project_root}")
logger.info(f"VERCEL={os.getenv('VERCEL')}, VERCEL_ENV={os.getenv('VERCEL_ENV')}")

try:
    from main import app as fastapi_app
    logger.info("Successfully imported main.app")
except Exception as e:
    logger.error(f"Failed to import main.app: {e}", exc_info=True)
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    fastapi_app = FastAPI(title="VetClaw (Fallback)")

    @fastapi_app.get("/")
    @fastapi_app.get("/{path:path}")
    async def error_handler(path: str = ""):
        return JSONResponse(
            status_code=503,
            content={"error": "Main app import failed", "detail": str(e)}
        )

try:
    from mangum import Mangum
    handler = Mangum(fastapi_app, lifespan="off")
    logger.info("Mangum handler created successfully")
except Exception as e:
    logger.error(f"Mangum handler creation failed: {e}", exc_info=True)
    raise
