"""
VetClaw - Vercel Serverless Entry Point
Direct ASGI export (Vercel Python runtime supports ASGI natively)
"""
import os
import sys
import traceback
import pathlib

# Path setup
project_root = str(pathlib.Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

os.environ.setdefault("DATABASE_PATH", "/tmp/vetclaw.db")

try:
    from main import app
except Exception as _e:
    # Diagnostic fallback
    from flask import Flask, jsonify
    app = Flask(__name__)

    @app.route("/")
    @app.route("/<path:path>")
    def _diag(path=""):
        return jsonify({
            "error": "VetClaw init failed",
            "detail": str(_e),
            "traceback": traceback.format_exc(),
            "python": sys.version,
            "path": sys.path[:5],
        }), 500
