"""
VetClaw - Vercel Ultra-Minimal Test
If this 500s too, the issue is Vercel config, not code.
"""
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok", "product": "VetClaw", "test": "ultra-minimal"}
