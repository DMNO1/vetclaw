"""
VetClaw - Vercel Serverless Adapter
Wraps the FastAPI app for Vercel Python runtime via Mangum
"""
import os
import sys

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mangum import Mangum
from main import app

# Mangum adapter for ASGI (FastAPI) -> AWS Lambda / Vercel serverless
handler = Mangum(app, lifespan="off")
