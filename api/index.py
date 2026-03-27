"""
VetClaw - Vercel Serverless Entry Point
Direct ASGI export - Vercel Python runtime supports ASGI natively
"""
import os
import sys
import pathlib

# Path setup
project_root = str(pathlib.Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

os.environ.setdefault("DATABASE_PATH", "/tmp/vetclaw.db")

# Import FastAPI app directly - Vercel supports ASGI
from main import app
