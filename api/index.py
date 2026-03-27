"""
VetClaw - Vercel Serverless Entry Point (Diagnostic)
Simplest possible app to isolate the 500 error
"""
import os
import sys
import traceback

# Path setup
import pathlib
project_root = str(pathlib.Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from flask import Flask, jsonify
    app = Flask(__name__)

    @app.route("/")
    @app.route("/<path:path>")
    def index(path=""):
        # Try importing main app components
        diagnostics = {"flask": "ok", "project_root": project_root}
        try:
            from main import app as main_app
            diagnostics["main_import"] = "ok"
            diagnostics["main_type"] = str(type(main_app))
        except Exception as e:
            diagnostics["main_import"] = "FAIL"
            diagnostics["main_error"] = str(e)
            diagnostics["main_traceback"] = traceback.format_exc()

        try:
            import mangum
            diagnostics["mangum"] = "ok"
        except Exception as e:
            diagnostics["mangum"] = f"FAIL: {e}"

        try:
            import yaml
            diagnostics["pyyaml"] = "ok"
        except Exception as e:
            diagnostics["pyyaml"] = f"FAIL: {e}"

        return jsonify(diagnostics)

except Exception as e:
    # Absolute last resort
    from http.server import BaseHTTPRequestHandler
    import io

    class app:
        """WSGI callable fallback"""
        def __init__(self, environ, start_response):
            self.environ = environ
            self.start = start_response

        def __iter__(self):
            body = f"Flask import failed: {e}\n{traceback.format_exc()}".encode()
            self.start("500 Internal Server Error", [("Content-Type", "text/plain")])
            yield body
