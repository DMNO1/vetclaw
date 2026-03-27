"""
VetClaw - Vercel Serverless Entry Point
Vercel Python runtime natively supports FastAPI ASGI apps.
Export `app` directly — no Mangum wrapper needed.
"""
import os
import sys

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import app
