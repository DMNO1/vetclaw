"""
VetClaw - Vercel Serverless Entry Point
ASGI to WSGI conversion for Vercel Python runtime
"""
import os
import sys
import pathlib
import traceback

# Path setup
project_root = str(pathlib.Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

os.environ.setdefault("DATABASE_PATH", "/tmp/vetclaw.db")

# Try a2wsgi first, fallback to Flask proxy
try:
    from main import app as asgi_app
    from a2wsgi import ASGIMiddleware
    app = ASGIMiddleware(asgi_app)
except Exception as e:
    # Create error-reporting Flask app
    from flask import Flask, jsonify
    app = Flask(__name__)
    
    @app.route("/")
    @app.route("/<path:path>")
    def error_handler(path=""):
        return jsonify({
            "error": "Failed to initialize VetClaw",
            "detail": str(e),
            "traceback": traceback.format_exc(),
            "sys_path": sys.path[:5],
            "cwd": os.getcwd(),
        }), 500
