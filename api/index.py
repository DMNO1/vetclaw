"""
VetClaw - Vercel Serverless Entry Point
ASGI to WSGI conversion for Vercel Python runtime
"""
import os
import sys
import pathlib

# Path setup
project_root = str(pathlib.Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

os.environ.setdefault("DATABASE_PATH", "/tmp/vetclaw.db")

# Import FastAPI app
from main import app as asgi_app

# Convert ASGI to WSGI using asgiref
try:
    from asgiref.wsgi import WsgiToAsgi
    # Actually we need AsgiToWsgi, but asgiref doesn't have that
    # Use a2wsgi instead
    from a2wsgi import ASGIMiddleware
    app = ASGIMiddleware(asgi_app)
except ImportError:
    # Fallback: use Flask to proxy
    from flask import Flask, request, Response
    import asyncio
    from fastapi.testclient import TestClient
    
    flask_app = Flask(__name__)
    client = TestClient(asgi_app, raise_server_exceptions=False)
    
    @flask_app.route("/", defaults={"path": ""})
    @flask_app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
    def proxy(path):
        method = request.method.lower()
        headers = {k: v for k, v in request.headers if k.lower() not in ['host', 'content-length']}
        
        try:
            if method == "get":
                resp = client.get(f"/{path}", headers=headers, params=request.args.to_dict())
            elif method == "post":
                resp = client.post(f"/{path}", headers=headers, 
                                 content=request.get_data(),
                                 params=request.args.to_dict())
            elif method == "put":
                resp = client.put(f"/{path}", headers=headers,
                                content=request.get_data(),
                                params=request.args.to_dict())
            elif method == "delete":
                resp = client.delete(f"/{path}", headers=headers, params=request.args.to_dict())
            else:
                resp = client.get(f"/{path}", headers=headers, params=request.args.to_dict())
            
            return Response(
                response=resp.content,
                status=resp.status_code,
                headers=[(k, v) for k, v in resp.headers.items()],
            )
        except Exception as e:
            import traceback
            return Response(
                response=f"Error: {str(e)}\n{traceback.format_exc()}".encode(),
                status=500,
            )
    
    app = flask_app
