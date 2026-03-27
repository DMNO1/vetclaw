"""
VetClaw - Vercel Serverless Entry Point
Wraps the FastAPI app for Vercel Python runtime using Mangum (ASGI→WSGI)
"""
import os
import sys
import logging
import pathlib

logger = logging.getLogger("vetclaw.vercel")

# Ensure project root is in path
project_root = str(pathlib.Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

os.environ.setdefault("DATABASE_PATH", "/tmp/vetclaw.db")

try:
    from main import app
    from mangum import Mangum
    handler = Mangum(app, lifespan="off")
    logger.info("VetClaw handler created successfully")
except Exception as e:
    logger.error(f"VetClaw app import failed: {e}", exc_info=True)
    # Diagnostic fallback
    from flask import Flask, jsonify
    import traceback
    _fallback = Flask(__name__)

    @_fallback.route("/")
    @_fallback.route("/<path:path>")
    def _diag(path=""):
        return jsonify({
            "error": "VetClaw init failed",
            "detail": str(e),
            "traceback": traceback.format_exc(),
            "python": sys.version,
            "path": sys.path[:5],
        }), 500

    handler = _fallback
