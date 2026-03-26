"""
VetClaw - Vercel Serverless Adapter
Wraps the FastAPI app for Vercel Python runtime via Mangum
"""
import os
import sys

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import app

# Vercel @vercel/python auto-detects FastAPI 'app' directly
# No Mangum wrapper needed - Vercel handles ASGI natively
